from datetime import datetime

import requests
from django.utils import timezone
from social_core.exceptions import AuthForbidden

from authapp.models import ShopUserProfile


def save_user_profile(backend, user, response, *args, **kwargs):
    if backend.name != 'vk-oauth2':
        return

    params = f"fields=bdate,sex,about,photo_max_orig&v=5.131&access_token={response['access_token']}"
    api_url = f"https://api.vk.com/method/users.get?{params}"

    vk_response = requests.get(api_url)

    if vk_response != 200:
        return

    vk_data = vk_response.json()['response'][0]

    if vk_data['sex']:
        if vk_data['sex'] == 2:
            user.shopuserprofile.gender = ShopUserProfile.MALE
        elif vk_data['sex'] == 1:
            user.shopuserprofile.gender = ShopUserProfile.FEMALE

    if vk_data['about']:
        user.shopuserprofile.about_me = vk_data['about']

    if vk_data['bdate']:
        b_date = datetime.strptime(vk_data['bdate'], '%d.%m.%Y').date()
        age = timezone.now().date().year - b_date.year
        if age < 18:
            user.delete()
            raise AuthForbidden('social_core.backends.vk.VKOAuth2')
        user.age = age

    # if vk_data['photo_max_orig']:
    #     print()
    #     photo_link = vk_data['photo_max_orig']
    #     photo_response = requests.get(photo_link)
    #     user_photo_path = f"users_images/{user.pk}.jpg"
    #     with open(f'media/{user_photo_path}', 'wb') as photo_file:
    #         photo_file.write(photo_response.content)
    #     user.avatar = user_photo_path

    user.save()


def get_avatar(backend, response, user, *args, **kwargs):
    url = None
    if backend.name == 'vk-oauth2':
        url = response.get('photo', '')
    if url:
        user.image = url
        user.save()
