from typing import List, Sequence
from sqlalchemy import select, delete, func

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
    HumanMessage,
    AIMessage,
)

from core.db import AsyncSessionLocal, ChatMessage
from core.metrics import DB_OP_COUNT, DB_QUERY_LATENCY

class PostgresAsyncChatMessageHistory(BaseChatMessageHistory):

    def __init__(self, session_id: str):
        self.session_id = session_id

    async def aget_messages(self) -> List[BaseMessage]:
        async with AsyncSessionLocal() as session:
            stmt = select(ChatMessage).where(
                ChatMessage.session_id == self.session_id
            ).order_by(ChatMessage.created_at.asc())
            
            DB_OP_COUNT.labels(operation="select_messages").inc()
            with DB_QUERY_LATENCY.labels(operation="select_messages").time():
                result = await session.execute(stmt)
            message_dicts = [item.message for item in result.scalars().all()]
            return messages_from_dict(message_dicts)

    async def aadd_messages(self, messages: Sequence[BaseMessage]) -> None:
        async with AsyncSessionLocal() as session:
            DB_OP_COUNT.labels(operation="insert_messages").inc()
            with DB_QUERY_LATENCY.labels(operation="insert_messages").time():
                session.add_all(
                    [
                        ChatMessage(
                            session_id=self.session_id,
                            message=message_to_dict(message),
                        )
                        for message in messages
                    ]
                )
                await session.commit()

    async def aclear(self) -> None:
        async with AsyncSessionLocal() as session:
            stmt = delete(ChatMessage).where(ChatMessage.session_id == self.session_id)
            DB_OP_COUNT.labels(operation="delete_messages").inc()
            with DB_QUERY_LATENCY.labels(operation="delete_messages").time():
                await session.execute(stmt)
                await session.commit()

    async def get_interaction_count(self) -> int:
        async with AsyncSessionLocal() as session:
            stmt = select(func.count(ChatMessage.id)).where(
                ChatMessage.session_id == self.session_id
            )
            DB_OP_COUNT.labels(operation="count_messages").inc()
            with DB_QUERY_LATENCY.labels(operation="count_messages").time():
                result = await session.execute(stmt)
            total_messages = result.scalar_one_or_none() or 0
            return total_messages // 2

    @property
    def messages(self):
        raise NotImplementedError(
            "This is an async history. Use 'aget_messages' instead."
        )

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        raise NotImplementedError(
            "This is an async history. Use 'aadd_messages' instead."
        )

    def clear(self) -> None:
        raise NotImplementedError(
            "This is an async history. Use 'aclear' instead."
        )
