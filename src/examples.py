"""Curated example requirements that demonstrate the splitter across domains."""

from __future__ import annotations

EXAMPLES: dict[str, str] = {
    "E-commerce: Wishlist": (
        "We want logged-in customers to save products to a wishlist so they "
        "can come back later and easily move items to cart. Wishlists should "
        "be private by default but shareable via link. Limit 100 items per "
        "wishlist. We also want to show wishlist size on the user's profile "
        "page, and notify users when a wishlisted item drops in price."
    ),
    "Automotive: OTA update opt-in": (
        "For Connected-Car users we need an opt-in flow for over-the-air "
        "software updates. Driver must consent in-vehicle or via the mobile "
        "app. Updates should only download on Wi-Fi by default and must be "
        "cancellable before installation starts. Compliance team requires "
        "audit logs of all consent changes, including who, when, and from "
        "which interface. The UI must be available in EN/DE/ZH."
    ),
    "Internal tool: Meeting recap": (
        "Build an internal tool where any employee can upload a meeting "
        "recording (mp3/mp4, up to 500MB). The tool transcribes (zh/en), "
        "generates a 5-bullet summary, extracts action items with owners "
        "and due dates, and emails the recap to all attendees. Recordings "
        "should be deleted after 30 days to comply with retention policy. "
        "Users should be able to edit the recap before it's emailed."
    ),
}
