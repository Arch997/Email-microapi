from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import action

from drf_yasg.utils import swagger_auto_schema
from sendgrid import SendGridAPIClient
from .serializers import MailSerializer, TemplateMailSerializer, UserSerializer, PasswordResetSerializer
from send_email_microservice.settings import SENDGRID_API_KEY
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from datetime import datetime, timedelta
from rest_auth.views import PasswordResetView

from django.conf import settings
from django.core.cache.backends .base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import User


# CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

MAIL_RESPONSES = {
    '200': 'Mail sent successfully.',
    '400': 'Incorrect request format.',
    '500': 'An error occurred, could not send email.',
    '401': 'An error occurred. Unauthorized.'
}


class UserCreate(APIView):
    """ 
    Creates the user. 
    """
    @swagger_auto_schema(
        request_body=UserSerializer,
        operation_description="Create an account to generate a token",
    )
   
    def post(self, request, format='json'):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.create(user=user)

            resp = { 'status': 'success', 'data': { 'message': 'Account created successfully.' } }
            resp['data']['account_id'] = user.username
            resp['data']['access_token'] = token.key

            return Response(resp, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class PasswordReset(APIView):
    """Sends a notification if password reset is suuccessful."""

    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(
        request_body = PasswordResetSerializer,
        operation_description = "Change your password",
    )
    
    def patch(self, request, pk=None):
        serializer = PasswordResetSerializer(User, data=request.data)
        
        if serializer.is_valid():
            # token = Token.objects.create(user=user)
            serializer.save()

            resp = {'status': 'success', 'data': {'message': 'FPassword changed successfully'} }
            resp['data']['account_id'] = user.id
            # resp['data']['access_token'] = token.key

            return Response(resp, status=status.HTTP_205_RESET_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        ''' if not user.check_password(request.data.get('password')):
            return Response({'password': ['Password is incorrect']}, 
            status=status.HTTP_400_BAD_REQUEST) 
        
        else:
            resp = {'status': 'success', 'data': {'message': 'Follow the link to change your password.'} }
            resp['data']['email_id'] = user.email
            resp['data']['access_token'] = token.key
        
            return Response(resp, status=status.HTTP_205_RESET_CONTENT)
            
        user.set_password(request.data.get('new_password'))
        user.save()
        resp = {'status': 'success', 'data': {'message': 'Password changed successfully'}}
        return Response(resp, status=status.HTTP_200_OK)    '''     


class SendMail(APIView):

    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=MailSerializer,
        operation_description="Sends email as plain text to recipient from sender.",
        responses=MAIL_RESPONSES
    )
    
    def post(self, request):
        mail_sz = MailSerializer(data=request.data)
        if mail_sz.is_valid():
            return send_email(request, mail_sz.validated_data)
        else:
            return Response({
                'status': 'failure',
                'data': { 'message': 'Incorrect request format.', 'errors': mail_sz.errors}
            }, status=status.HTTP_400_BAD_REQUEST)

            
class SendMailWithTemplate(APIView):

    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=TemplateMailSerializer,
        operation_description="Sends email as HTML template to recipient from sender.",
        responses=MAIL_RESPONSES
    )
    
    def post(self, request):
        template_mail_sz = TemplateMailSerializer(data=request.data)
        if template_mail_sz.is_valid():
            return send_email(request, template_mail_sz.validated_data, is_html_template=True)
        else:
            return Response({
                'status': 'failure',
                'data': { 'message': 'Incorrect request format.', 'errors': template_mail_sz.errors}
            }, status=status.HTTP_400_BAD_REQUEST)



class SendScheduledMail(APIView):

    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=MailSerializer,
        operation_description="Sends email as plain text to recipient from sender.",
        responses=MAIL_RESPONSES
    )
    
    def post(self, request):
        mail_sz = MailSerializer(data=request.data)
        if mail_sz.is_valid():
            return send_email(request, mail_sz.validated_data,False,True)
        else:
            return Response({
                'status': 'failure',
                'data': { 'message': 'Incorrect request format.', 'errors': mail_sz.errors}
            }, status=status.HTTP_400_BAD_REQUEST)

            
def send_email(request, options, is_html_template=False, scheduled=False):

    def get_email_dict(emails, delimeter):
        return [{'email': email.strip()} for email in emails.split(delimeter)]

    body_type = 'text/plain'
    body = ''

    if is_html_template:
        body_type = 'text/html'
        body = options['htmlBody']
    else:
        body = options['body']

    #to send the mail at a scheduled date
    if(scheduled):
        #get today's date 
        current_time = datetime.now()
        hours = int(options['hour'])
        hours_to_add = timedelta(hours = hours)
        later_time = current_time + hours_to_add
        #convert the time to timestamp
        later_timestamp = datetime.timestamp(later_time)
        data = {
        'personalizations': [{
            'to': [{'email': options['recipient']}],
            'subject': options['subject'],
            'send_at': later_timestamp
        }],
        'from': {'email': request.user.email},
        'content': [{
            'type': body_type,
            'value': body
        }],
    }
    else:
        data = {
        'personalizations': [{
            'to': [{'email': options['recipient']}],
            'subject': options['subject']
        }],
        'from': {'email': request.user.email},
        'content': [{
            'type': body_type,
            'value': body
        }],
    }

    if len(options['cc']) > 0:
        data['personalizations'][0]['cc'] = get_email_dict(options['cc'], ',')

    if len(options['bcc']) > 0:
        data['personalizations'][0]['bcc'] = get_email_dict(options['bcc'], ',')

    sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
    try: sg.client.mail.send.post(request_body=data)
    except:
        return Response({
            'status': 'failure',
            'data': { 'message': 'An error occurred, could not send email.'}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'status': 'success',
        'data': { 'message': 'Mail sent successfully.'}
    }, status=status.HTTP_200_OK)



