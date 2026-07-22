"""Shared neumorphic widget classes for Django forms (presentation only)."""

from __future__ import annotations

from django import forms

NEO_CONTROL = (
    "w-full rounded-2xl bg-surface px-4 py-2.5 text-sm text-ink "
    "shadow-neo-inset border-0 outline-none transition-all duration-300 ease-in-out "
    "focus:ring-2 focus:ring-brand"
)

NEO_CHECKBOX = (
    "h-4 w-4 rounded shadow-neo-inset border-0 text-brand "
    "transition-all duration-300 ease-in-out focus:ring-2 focus:ring-brand"
)

NEO_SELECT = NEO_CONTROL

NEO_TEXTAREA = (
    "w-full min-h-[5rem] rounded-2xl bg-surface px-4 py-2.5 text-sm text-ink "
    "shadow-neo-inset border-0 outline-none transition-all duration-300 ease-in-out "
    "focus:ring-2 focus:ring-brand"
)


def apply_neumorphic_widgets(form: forms.BaseForm) -> None:
    """Attach Tailwind neumorphic classes to visible form widgets."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.HiddenInput):
            continue
        existing = widget.attrs.get("class", "")
        if isinstance(widget, forms.CheckboxInput):
            css = NEO_CHECKBOX
        elif isinstance(widget, forms.Select):
            css = NEO_SELECT
        elif isinstance(widget, forms.Textarea):
            css = NEO_TEXTAREA
        else:
            css = NEO_CONTROL
        widget.attrs["class"] = f"{existing} {css}".strip()


class NeumorphicFormMixin:
    """Mixin that styles all visible widgets with neumorphic utilities."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        apply_neumorphic_widgets(self)
