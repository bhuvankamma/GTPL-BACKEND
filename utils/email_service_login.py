import boto3
from utils.config_login import SES_REGION, SES_SOURCE_EMAIL

ses = boto3.client("ses", region_name=SES_REGION)


def send_password_setup_email(to_email: str, token: str):
    link = f"https://frontend.app/set-password?token={token}"

    ses.send_email(
        Source=SES_SOURCE_EMAIL,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": "Set up your HRMS password"},
            "Body": {
                "Text": {
                    "Data": f"Set your password (valid 24h): {link}"
                }
            }
        }
    )
