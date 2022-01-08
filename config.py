SERVICE_IDS: dict[int, int] = {
    1234: 12345678910,
    4321: 10987654321,
}  # Service ID: Killfeed Channel ID
MAPS: dict[int, str] = {
    1234: "livonia",
    4321: "chernarus",
}  # Service ID: livonia or chernarus
DESIGN: dict[int, tuple] = {
    1234: ("https://iili.io/YrKbou.md.png", 0xFF0000),
    4321: ("https://iili.io/YrKbou.md.png", 0xFF0000),
}  # Service ID: (Thumbnail URL, Colour) If you don't want a Thumbnail replace it with ""
NITRADO_TOKENS: dict[int, str] = {
    1234: "Bearer YourNitradoTokenGoesIntoHere",
    4321: "Bearer YourNitradoTokenGoesIntoHere",
}  # Service ID: Nitrado Token
DISCORD_BOT_TOKEN: str = (
    "YourDiscordBotToken"  # Your Discord Bot Token goes into here
)

# REPLACE THOSE EXAMPLES WITH YOUR SERVER / YOUR SERVERS
