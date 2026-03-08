from backend.models import DigestContent

# Category-specific fallback checklists — used when AI is unavailable.
# Each checklist is calm, empowering, and actionable.
FALLBACKS: dict[str, DigestContent] = {
    "cyber_threat": DigestContent(
        summary="A cyber threat such as phishing or a data breach has been detected in your area.",
        steps=[
            "Change your passwords immediately — start with email, banking, and social media.",
            "Enable two-factor authentication on all critical accounts.",
            "Monitor your bank statements and credit report for unusual activity over the next 30 days.",
        ],
    ),
    "scam_alert": DigestContent(
        summary="A scam targeting community members has been reported.",
        steps=[
            "Do not respond to unsolicited calls, texts, or emails asking for money or personal info.",
            "Verify the identity of anyone claiming to be from a government agency by calling their official number.",
            "Report the scam to the FTC at reportfraud.ftc.gov to help protect others.",
        ],
    ),
    "local_crime": DigestContent(
        summary="A local crime incident has been reported in your area.",
        steps=[
            "Stay aware of your surroundings and report any suspicious activity to your local non-emergency line.",
            "Ensure your home is secure — check that doors, windows, and exterior lights are working.",
            "Connect with your Neighborhood Watch or local community group to stay informed.",
        ],
    ),
    "infrastructure": DigestContent(
        summary="An infrastructure outage affecting your area has been reported.",
        steps=[
            "Use battery-powered devices and keep your phone charged in case of extended outage.",
            "Check your local government's emergency alert system for restoration updates.",
            "Never use generators, grills, or camp stoves indoors — carbon monoxide is deadly.",
        ],
    ),
    "general": DigestContent(
        summary="A community safety alert has been reported in your area.",
        steps=[
            "Stay informed by following your local news and official emergency services.",
            "Check in with neighbours, especially elderly or vulnerable residents.",
            "Report any concerning activity to local authorities.",
        ],
    ),
}


def get_fallback(category: str) -> DigestContent:
    return FALLBACKS.get(category, FALLBACKS["general"])
