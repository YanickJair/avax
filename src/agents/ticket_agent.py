from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import Tool

from src.customers.service import CustomerService
from src.models.common import ObjectIdField
from src.tickets.models import TicketCategory, TicketSchema
from src.tickets.service import TicketService


class TicketAgent:
    """Ticket agent. This agent is responsible for managing tickets like creation, filtering and more.

    It receives a ticket service.
    """
    def __init__(self, ticket_service: TicketService, customer_service: CustomerService) -> None:
        self.ticket_service = ticket_service
        self.customer_service = customer_service
        self.categories = [category for category in TicketCategory]

        self.llm = ChatAnthropic(
            model_name="claude-3-sonnet-20240229",
            temperature=0,
            timeout=30,
            max_retries=2,
            stop=["\n\nHuman:", "\n\nAssistant:"],
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()

    def _create_tools(self) -> list[Tool]:
        return [
            Tool(
                name="create_ticket",
                description="Create a new ticket for a customer. Args: customer Id, subject, and description",
                func=self._tool_create_ticket
            ),
            Tool(
                name="check_customer_history",
                description="Check customer previous interaction. It can be through other channels and old tickets",
                func=None
            ),
            Tool(
                name="analyze_ticket",
                description="Based on ticket's subject and description assign category and priority",
                func=self._tool_analyze_ticket
            )
        ]

    async def _tool_create_ticket(self, ticket) -> TicketSchema:
        return await self.ticket_service.create(ticket)

    def _create_agent(self) -> AgentExecutor:
        """Create the agent based on tools we define previously"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a ticket management assistant for AvX.
            Your role is to help process and manage support tickets effectively.
            
            {tools}
            Available tools: {tool_names}
            
            Use the available tools to:
            1. Analyze and categorize tickets
            2. Check customer history
            3. Suggest appropriate responses
            4. Update tickets with your analysis
            
            {agent_scratchpad}
            """),
            ("human", "{input}"),
            ("assistant", "I'll help process this ticket. Let me analyze it step by step.")
        ])

        agent = create_structured_chat_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

    async def _tool_analyze_ticket(self, ticket_id: ObjectIdField) -> TicketSchema | None:
        try:
            ticket = await self.ticket_service.find_one(ticket_id)

            if ticket:
                category = await self._suggest_category(ticket.subject, ticket.description)
                priority = await self._suggest_priority(ticket.subject, ticket.description)

                return await self.ticket_service.update_ticket_analysis(
                    ticket_id,
                    category=category,
                    priority=priority
                )
        except Exception as exc:
            raise exc

    async def _suggest_category(self, subject: str, description: str | None) -> str:
        """Analyze ticket content and suggest appropriate category."""
        prompt = f"""
        Based on this support ticket, suggest the most appropriate category.
        Available categories: {', '.join(self.categories)}

        Subject: {subject}
        Description: {description}

        Consider:
        - Billing: Issues related to payments, invoices, or subscription
        - Technical: Technical problems, bugs, or system issues
        - General: General inquiries or non-specific questions
        - Feature Request: Suggestions for new features or improvements

        Respond with only the category name in lowercase.
        The category must be exactly one of: {', '.join(self.categories)}
        """
        response = await self.llm.ainvoke([{
            "role": "user",
            "content": prompt
        }])
        if isinstance(response, list):
            suggested_category = str(response[0].get('content', '')).strip().lower()
        else:
            suggested_category = str(response).strip().lower()

        if suggested_category not in self.categories:
            return TicketCategory.GENERAL.value

        return suggested_category

    async def _suggest_priority(self, subject: str, description: str | None) -> str:
        """Analyze ticket content and suggest priority level."""
        prompt = f"""
        Analyze this support ticket and suggest the appropriate priority level.
        Available priorities: low, medium, high, urgent

        Consider:
        - System downtime or critical failures
        - Financial impact
        - Number of affected users
        - Security concerns

        Subject: {subject}
        Description: {description}

        Respond with only the priority level in lowercase.
        """

        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])

        if isinstance(response, list):
            return str(response[0].get('content', '')).strip().lower()
        return str(response).strip().lower()

