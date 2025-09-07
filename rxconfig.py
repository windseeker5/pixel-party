import reflex as rx

config = rx.Config(
    app_name="PixelParty",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)