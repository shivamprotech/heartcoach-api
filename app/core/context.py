# app/core/context.py
import contextvars

current_user_id = contextvars.ContextVar("current_user_id", default=None)
