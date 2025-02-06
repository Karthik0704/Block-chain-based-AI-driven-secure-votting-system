from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('register/', views.register_user, name='register_user'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login_view, name='login_view'),
    path('face-recognition/', views.face_recognition_page, name='face_recognition_page'),
    path('face-verification/', views.face_verification, name='face_verification'),
    path('voting-page/', views.voting_page, name='voting_page'),
    path('cast-vote/', views.cast_vote, name='cast_vote'),
    path('logout/', views.logout_view, name='logout_view'),
    #path('generate-qr/', views.generate_qr_code, name='generate_qr_code'),
    # path('mobile-verify/', views.process_mobile_verification, name='mobile_verify'),
    # # urls.py
    # path('mobile-verification/', views.mobile_verification, name='mobile_verification'),
    path('mobile-verify/', views.process_mobile_verification, name='mobile_verify'),
    path('send-verification-link/', views.send_verification_link, name='send_verification_link'),
    path('contact-developer/', views.contact_developer, name='contact_developer'),
    # path('results/', views.election_results, name='election_results'),
    path('results/', views.protected_results, name='election_results'),
    path('auth/results/', views.election_results, name='election_results'),
    




    
]
