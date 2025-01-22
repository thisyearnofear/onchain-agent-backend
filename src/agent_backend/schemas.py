from marshmallow import Schema, fields, validate

class ChatRequestSchema(Schema):
    """Schema for validating chat requests."""
    input = fields.String(required=True, validate=validate.Length(min=1))
    conversation_id = fields.String(required=True, validate=validate.Length(min=1))

chat_request_schema = ChatRequestSchema() 