"""Compatibility shim for legacy imports.

The PDF merge routes now live in app.tools.pdf.router.
"""

from app.tools.pdf.router import router

__all__ = ["router"]
