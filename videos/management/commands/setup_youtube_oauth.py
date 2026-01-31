"""
Management command to set up YouTube OAuth credentials.

Usage:
    python manage.py setup_youtube_oauth

This command guides you through the OAuth flow to obtain and store
YouTube API credentials for video uploads.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Set up YouTube OAuth credentials for video uploads'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='main_channel',
            help='Name for the credential set (default: main_channel)'
        )
        parser.add_argument(
            '--redirect-uri',
            type=str,
            default='http://localhost:8000/api/videos/oauth/callback/',
            help='OAuth redirect URI'
        )

    def handle(self, *args, **options):
        from videos.services.youtube_service import (
            get_oauth_authorization_url,
            exchange_oauth_code,
        )
        from videos.models import YouTubeCredential
        
        name = options['name']
        redirect_uri = options['redirect_uri']
        
        self.stdout.write(self.style.WARNING(
            '\n' + '='*60 + '\n'
            'YouTube OAuth Setup\n'
            '='*60 + '\n'
        ))
        
        self.stdout.write(
            'This command will guide you through setting up YouTube API credentials.\n'
            '\nPrerequisites:\n'
            '1. Create a project in Google Cloud Console\n'
            '2. Enable YouTube Data API v3\n'
            '3. Create OAuth 2.0 credentials (Web application)\n'
            '4. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in your .env\n'
            '\n'
        )
        
        # Check for existing credential
        existing = YouTubeCredential.objects.filter(name=name).first()
        if existing:
            self.stdout.write(self.style.WARNING(
                f'Credential "{name}" already exists. '
                'Continuing will overwrite the existing tokens.\n'
            ))
        
        try:
            # Generate authorization URL
            auth_url = get_oauth_authorization_url(redirect_uri)
            
            self.stdout.write(self.style.SUCCESS(
                '\nStep 1: Open this URL in your browser and authorize:\n'
            ))
            self.stdout.write(f'\n{auth_url}\n\n')
            
            self.stdout.write(
                'After authorization, you will be redirected to a URL like:\n'
                f'{redirect_uri}?code=AUTHORIZATION_CODE\n\n'
            )
            
            # Get authorization code from user
            code = input('Enter the authorization code from the redirect URL: ').strip()
            
            if not code:
                self.stdout.write(self.style.ERROR('No code provided. Aborting.'))
                return
            
            # Exchange code for tokens
            self.stdout.write('\nExchanging code for tokens...')
            tokens = exchange_oauth_code(code, redirect_uri)
            
            # Create or update credential
            if existing:
                existing.access_token = tokens['access_token']
                existing.refresh_token = tokens['refresh_token']
                existing.token_expiry = tokens.get('expires_at')
                existing.save()
                credential = existing
            else:
                credential = YouTubeCredential.objects.create(
                    name=name,
                    access_token=tokens['access_token'],
                    refresh_token=tokens['refresh_token'],
                    token_expiry=tokens.get('expires_at'),
                    is_active=True,
                )
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ YouTube credentials saved successfully!\n'
                f'  Name: {name}\n'
                f'  ID: {credential.id}\n'
            ))
            
            self.stdout.write(
                '\nYou can now upload videos to YouTube using the API.\n'
                'The refresh token will automatically renew access tokens.\n'
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {e}'))
            raise

