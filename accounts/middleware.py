"""
Tracking user visits, page views, and activity using sessions and cookies
"""

from django.utils import timezone
from django.contrib.sessions.models import Session
from datetime import datetime, timedelta
import json


class ActivityTrackingMiddleware:
    """
    Middleware to track user activity using sessions and cookies.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request before view
        self.track_activity(request)

        # Get response from view
        response = self.get_response(request)

        # Process response after view
        self.update_activity(request, response)

        return response

    def track_activity(self, request):
        """Track user activity at the start of request"""

        # Initialize session variables if they don't exist
        if 'activity' not in request.session:
            request.session['activity'] = {
                'first_visit': str(timezone.now()),
                'last_visit': str(timezone.now()),
                'page_views': 0,
                'pages_visited': [],
                'tips_viewed': [],
                'daily_visits': {}
            }

        # Getting current activity data
        activity = request.session['activity']

        # Updating last visit
        activity['last_visit'] = str(timezone.now())

        # Tracking daily visits
        today = timezone.localtime(timezone.now()).date().isoformat()
        if 'daily_visits' not in activity:
            activity['daily_visits'] = {}

        if today not in activity['daily_visits']:
            activity['daily_visits'][today] = 0

        activity['daily_visits'][today] += 1

        # Cleaning up old daily visits (keep last 30 days)
        self.cleanup_old_visits(activity)

        # Saveing back to session
        request.session['activity'] = activity
        request.session.modified = True

    def update_activity(self, request, response):
        """Updating activity after view processing"""

        if 'activity' in request.session:
            activity = request.session['activity']

            # Increment page views
            activity['page_views'] = activity.get('page_views', 0) + 1

            # Tracking current page
            current_page = request.path
            if 'pages_visited' not in activity:
                activity['pages_visited'] = []

            # Keeping last 50 pages visited
            activity['pages_visited'].append({
                'url': current_page,
                'timestamp': str(timezone.now()),
                'method': request.method
            })

            if len(activity['pages_visited']) > 50:
                activity['pages_visited'] = activity['pages_visited'][-50:]

            # Save back to session
            request.session['activity'] = activity
            request.session.modified = True

        # Setting cookie for returning visitor
        if response.status_code == 200:
            response.set_cookie(
                'returning_visitor',
                'true',
                max_age=30 * 24 * 60 * 60,  # 30 days
                httponly=True,
                samesite='Lax'
            )

    def cleanup_old_visits(self, activity):
        """Removing visit data older than 30 days"""
        if 'daily_visits' in activity:
            cutoff_date = (timezone.localtime(timezone.now()).date() - timedelta(days=30)).isoformat()
            activity['daily_visits'] = {
                date: count
                for date, count in activity['daily_visits'].items()
                if date >= cutoff_date
            }
