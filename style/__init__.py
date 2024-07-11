import os

css_path = os.path.join(os.path.dirname(__file__), 'style.css')

with open(css_path) as f:
    css = f.read()


custom_css = f"<style>{css}</style>"


__all__ = ["custom_css"]
