"""Deprecated security helpers.

Password hashing and custom JWTs are no longer used. Supabase Auth handles
authentication, and the backend only validates Supabase JWTs in
app.auth.dependencies.
"""
