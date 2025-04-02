from datetime import datetime, timedelta

import requests
from aiohttp import web
from aiohttp.web import middleware

from server import db, config
from server.db import models
from .security import validate_api_key


class AnonymousUser:
    is_anonymous = True


@middleware
async def is_user_authenticated(request, handler):
    # Validate API-key
    api_key = request.headers.get("X-API-Key")
    if not api_key or not validate_api_key(api_key):
        return web.Response(status=401, reason="Invalid or missing API key")

    authorization_header = request.headers.get("Authorization")
    user_is_anonymous = True
    new_access_token = None
    if authorization_header:
        token_prefix = "token "
        if token_prefix in authorization_header:
            access_token = authorization_header[len(token_prefix):]
            with db.get_session() as session:
                oauth_token_db_record = (
                    session.query(models.OAuthToken)
                    .filter_by(access_token=access_token)
                    .first()
                )
                if oauth_token_db_record:
                    user_should_still_be_signed_in = True
                    if oauth_token_db_record.expires_at <= datetime.utcnow():
                        user_should_still_be_signed_in = False
                        print(
                            "The access token seems to have expired, based on the saved data in the db record."
                        )
                        if oauth_token_db_record.refresh_token_expires_at > datetime.utcnow():
                            new_access_token = get_new_access_token(oauth_token_db_record, session)
                            if new_access_token:
                                user_should_still_be_signed_in = True
                        else:
                            print("The refresh token also seems to have expired.")
                        clear_out_expired_oauth_token_records_for_this_user(oauth_token_db_record.user_id, session)
                    if user_should_still_be_signed_in:
                        user = session.query(models.User).filter_by(id=oauth_token_db_record.user_id).first()
                        if user:
                            request.user = user
                            user_is_anonymous = False
                        else:
                            return web.Response(
                                status=500,
                                reason="We have a record of the supplied access token and it has an associated user ID, but we couldn't find the associated user record with that ID.",
                            )
                else:
                    print("Unable to find a db record for the supplied access token.")
        else:
            print(
                "The request has an Authorization header, but it doesn't seem to have a value containing the necessary 'token ' prefix."
            )
    if user_is_anonymous:
        request.user = AnonymousUser()
    resp = await handler(request)
    if new_access_token:
        print("Setting the x-updated-access-token header to {}".format(new_access_token))
        resp.headers["x-updated-access-token"] = new_access_token
    return resp


def get_new_access_token(oauth_token_db_record, session):
    """
    To allow users to sign out of the app from their GitHub account (e.g. if they sign into an
    on-premise-deployed instance of the app from some shared computer and forget to sign out until
    they've gone back home, and so they want to sign out remotely), we need to make sure the access token
    we have is always up-to-date (not expired). Access tokens seem to last eight hours, at which point,
    if we try to get a new access token and the refresh token has been revoked, we'll know the user has
    signed out remotely (from their GitHub account).
    """
    new_access_token = None
    github_authorization_server_request_headers = {
        "Accept": "application/json"
    }
    params_to_trade_code_for_tokens = {
        "client_id": config.static.github_app.CLIENT_ID,
        "client_secret": config.static.github_app.CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": oauth_token_db_record.refresh_token,
        "redirect_uri": config.static.FRONTEND_BASE_URL,
    }
    print("Querying GitHub for a new access token by sending the saved refresh token.")
    github_response = requests.post(
        "https://github.com/login/oauth/access_token",
        params=params_to_trade_code_for_tokens,
        headers=github_authorization_server_request_headers,
    )
    response_data = github_response.json()

    # If the user revokes access to the app via their GitHub account, you won't get an error message from GitHub
    # saying specifically that, but instead it'll just tell you that the particular refresh token you're trying to use
    # is not valid. It'll be a 200 HTTP response.
    the_refresh_token_is_invalid = response_data.get("error") == "bad_refresh_token"
    if the_refresh_token_is_invalid:
        print("The refresh token appears to be invalid.")
        session.delete(oauth_token_db_record)
        session.commit()
    elif "access_token" in response_data:
        print("Updating the db record for this access token with the new one from GitHub.")
        oauth_token_db_record.access_token = response_data["access_token"]
        oauth_token_db_record.expires_at = datetime.utcnow() + timedelta(seconds=response_data["expires_in"])
        oauth_token_db_record.refresh_token = response_data["refresh_token"]
        oauth_token_db_record.refresh_token_expires_at = datetime.utcnow() + timedelta(
            seconds=response_data["refresh_token_expires_in"]
        )

        session.add(oauth_token_db_record)
        session.commit()
        new_access_token = response_data["access_token"]
    return new_access_token


def clear_out_expired_oauth_token_records_for_this_user(user_id, session):
    oauth_records_for_this_user = session.query(models.OAuthToken).filter_by(user_id=user_id).all()
    for record in oauth_records_for_this_user:
        if record.expires_at <= datetime.utcnow() and record.refresh_token_expires_at <= datetime.utcnow():
            print("Deleting expired oauth token record for user {}".format(user_id))
            session.delete(record)
            session.commit()
