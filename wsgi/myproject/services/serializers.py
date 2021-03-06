from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Item, Category, Location, UserRating
from .utils import get_coords, get_address

class CategoryField(serializers.RelatedField):

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, value):
        category = get_object_or_404(Category, name=value)
        return category

class LocationSerializer(serializers.ModelSerializer):
    location = serializers.CharField(allow_blank=True, required=False)
    long_position = serializers.CharField(allow_blank=True, required=False)
    lat_position = serializers.CharField(allow_blank=True, required=False)
    class Meta:
        model = Location
        fields = ('location', 'long_position', 'lat_position')

    def validate(self, location):
        if not 'location' in location or (not location['location'] and not location['long_position'] and not location['lat_position']):
            raise serializers.ValidationError('You must provide either location address or lat/long coordinates.')

        try:
            if not location['location']:
                location['location'] = get_address(location['lat_position'], location['long_position'])
            elif not location['lat_position'] or not location['long_position']:
                location['lat_position'], location['long_position'] = get_coords(location['location'])
        except Exception as e:
            print location
            print e
            raise serializers.ValidationError('Unable to get a valid location.')
        return super(LocationSerializer, self).validate(location)

class ItemSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    category = CategoryField(queryset=Category.objects.all(), label=_("Category"))
    owner = serializers.ReadOnlyField(source='owner.username')
    created = serializers.DateTimeField(read_only=True)
    expires_on = serializers.DateTimeField(required=False) #format="%d %b %Y %H:%M:%S"
    user_rating = serializers.SerializerMethodField('getRatings')

    class Meta:
        model = Item
        fields = ('id', 'name', 'description', 'deal', 'image', 'category', 'location', 'owner', 'created', 'expires_on', 'user_rating')

    def get_validation_exclusions(self):
        exclusions = super(ItemSerializer, self).get_validation_exclusions()

        return exclusions + ['expires_on']
    def getRatings(self, item):
        rating = UserRating.objects.filter(voted_user=item.owner).aggregate(Avg('punctuation'))
        return rating['punctuation__avg']

    def notify(self, item):
        msg_html = render_to_string(
                'email/newitem.html',
                {
                    'item': item.name,
                    'id': item.id,
                    'location': item.location.location,
                    'name': item.owner.first_name,
                    'image': item.image.url
                }
        )

        email = EmailMessage(
            item.owner.first_name + ' wants to publish ' + item.name,
            msg_html,
            to=settings.NOTIFY_EMAILS
        )
        email.content_subtype = "html"
        email.send()

    def create(self, validated_data):
        request = self.context.get('request', None)
        if request is not None:
            user = request.user
        else:
            return false

        address = validated_data['location']['location']
        lat = validated_data['location']['lat_position']
        lon = validated_data['location']['long_position']

        location = Location.objects.create(
            lat_position=lat,
            long_position=lon,
            location=address,
            )
        location.save()

        if not 'expires_on' in validated_data:
            validated_data['expires_on'] = None

        if not 'deal' in validated_data or not validated_data['deal']:
            validated_data['deal'] = _('I only ask you to give something away in this website and the item is yours.')

        # Create the item instance
        item = Item.objects.create(
            name=validated_data['name'],
            description=validated_data['description'],
            deal=validated_data['deal'],
            image=validated_data['image'],
            category=validated_data['category'],
            location=location,
            expires_on=validated_data['expires_on'],
            owner=user,
            language=get_language()
        )

        self.notify(item)

        return item
