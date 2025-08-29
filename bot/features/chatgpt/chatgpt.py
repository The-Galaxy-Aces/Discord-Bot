import asyncio
import discord
from discord.ext import commands
from bot.features.tgacog import TGACog
from openai import AsyncOpenAI


class ChatGPT(TGACog):
    """
    ChatGPT integration cog for Discord bot.
    Allows users to interact with OpenAI's ChatGPT API.
    """
    
    def __init__(self, bot):
        """
        Initialize the ChatGPT cog with OpenAI client
        """
        super().__init__(bot)
        
        # Required config parameters
        REQUIRED_PARAMS = ['api_key']
        self.process_config(self.bot, REQUIRED_PARAMS)
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.CONFIG.get('api_key')
        )
        
        # Configuration settings
        self.model = self.CONFIG.get('model', 'gpt-5')
        self.max_tokens = self.CONFIG.get('max_tokens', 2000)
        self.temperature = self.CONFIG.get('temperature', 0.7)
        self.system_message = self.CONFIG.get('system_message', 
            "You are a helpful assistant in a Discord server. Keep responses concise and friendly.")
        
        # Conversation memory (per user)
        self.conversations = {}
        self.max_conversation_length = self.CONFIG.get('max_conversation_length', 10)
        
        self.bot.log.info(f"ChatGPT cog initialized with model: {self.model}")

    def _get_conversation_key(self, ctx):
        """Generate a unique key for user conversations"""
        return f"{ctx.guild.id}_{ctx.author.id}" if ctx.guild else f"dm_{ctx.author.id}"

    def _get_conversation_history(self, conversation_key):
        """Get conversation history for a user"""
        if conversation_key not in self.conversations:
            self.conversations[conversation_key] = [
                {"role": "system", "content": self.system_message}
            ]
        return self.conversations[conversation_key]

    def _add_to_conversation(self, conversation_key, role, content):
        """Add a message to conversation history"""
        conversation = self._get_conversation_history(conversation_key)
        conversation.append({"role": role, "content": content})
        
        # Keep conversation within limits (excluding system message)
        if len(conversation) > self.max_conversation_length + 1:
            # Remove oldest non-system messages
            conversation = [conversation[0]] + conversation[-(self.max_conversation_length):]
            self.conversations[conversation_key] = conversation

    @commands.group(aliases=['gpt', 'ai'])
    @TGACog.check_permissions()
    async def chatgpt(self, ctx):
        """
        Main ChatGPT command group. Use subcommands to interact with ChatGPT.
        
        Examples:
        !chatgpt ask What is the meaning of life?
        !chatgpt clear  (to clear conversation history)
        !chatgpt help   (to see available commands)
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🤖 ChatGPT Commands",
                description="Use these commands to interact with ChatGPT:",
                color=0x00ff00
            )
            embed.add_field(
                name="!chatgpt ask <question>",
                value="Ask ChatGPT a question",
                inline=False
            )
            embed.add_field(
                name="!chatgpt clear",
                value="Clear your conversation history",
                inline=False
            )
            embed.add_field(
                name="!chatgpt status",
                value="Show current configuration",
                inline=False
            )
            await ctx.send(embed=embed)

    async def _ask_chatgpt(self, ctx, prompt: str):
        """
        Internal method to handle ChatGPT requests
        """
        if not prompt:
            await ctx.send("❌ Please provide a question or prompt!")
            return

        self.bot.log.info(f"ChatGPT ask command triggered by {ctx.author}: {prompt}")
        self.bot.log.info(f"Context guild: {ctx.guild.name if ctx.guild else 'DM'}")
        self.bot.log.info(f"Full message content: {ctx.message.content}")

        # Show typing indicator
        async with ctx.typing():
            try:
                conversation_key = self._get_conversation_key(ctx)
                
                # Add user message to conversation
                self._add_to_conversation(conversation_key, "user", prompt)
                
                # Get conversation history
                messages = self._get_conversation_history(conversation_key)
                
                self.bot.log.debug(f"ChatGPT request from {ctx.author}: {prompt}")
                
                # Make API call to OpenAI
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    user=str(ctx.author.id)
                )
                
                # Extract response content
                assistant_message = response.choices[0].message.content
                
                # Add assistant response to conversation
                self._add_to_conversation(conversation_key, "assistant", assistant_message)
                
                self.bot.log.debug(f"ChatGPT response: {assistant_message[:100]}...")
                
                # Send response (handle Discord's 2000 character limit)
                if len(assistant_message) <= 1900:  # Leave room for embed formatting
                    embed = discord.Embed(
                        title="🤖 ChatGPT Response",
                        description=assistant_message,
                        color=0x00ff00
                    )
                    embed.set_footer(text=f"Model: {self.model} | Requested by {ctx.author.display_name}")
                    await ctx.send(embed=embed)
                else:
                    # Split long responses
                    for i in range(0, len(assistant_message), 1900):
                        chunk = assistant_message[i:i+1900]
                        if i == 0:
                            embed = discord.Embed(
                                title="🤖 ChatGPT Response (Part 1)",
                                description=chunk,
                                color=0x00ff00
                            )
                        else:
                            embed = discord.Embed(
                                title=f"🤖 ChatGPT Response (Part {i//1900 + 1})",
                                description=chunk,
                                color=0x00ff00
                            )
                        await ctx.send(embed=embed)
                        await asyncio.sleep(0.5)  # Small delay between parts
                
            except Exception as e:
                self.bot.log.error(f"ChatGPT API error: {e}")
                embed = discord.Embed(
                    title="❌ ChatGPT Error",
                    description=f"Sorry, I encountered an error: {str(e)}",
                    color=0xff0000
                )
                await ctx.send(embed=embed)

    @chatgpt.command(aliases=['chat'])
    @TGACog.check_permissions()
    async def ask(self, ctx, *, prompt: str):
        """
        Ask ChatGPT a question and get a response.
        
        Usage: !chatgpt ask <your question>
        Example: !chatgpt ask Explain quantum physics in simple terms
        """
        await self._ask_chatgpt(ctx, prompt)

    @chatgpt.command()
    @TGACog.check_permissions()
    async def question(self, ctx, *, prompt: str):
        """
        Ask ChatGPT a question and get a response.
        
        Usage: !chatgpt question <your question>
        Example: !chatgpt question What is Python?
        """
        await self._ask_chatgpt(ctx, prompt)

    @chatgpt.command(aliases=['reset'])
    @TGACog.check_permissions()
    async def clear(self, ctx):
        """
        Clear your conversation history with ChatGPT.
        This starts a fresh conversation.
        """
        conversation_key = self._get_conversation_key(ctx)
        
        if conversation_key in self.conversations:
            del self.conversations[conversation_key]
            
        embed = discord.Embed(
            title="🗑️ Conversation Cleared",
            description="Your ChatGPT conversation history has been cleared.",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    @chatgpt.command()
    @TGACog.check_permissions()
    async def test(self, ctx):
        """Test command to verify ChatGPT cog is working"""
        await ctx.send("✅ ChatGPT cog is working! You can use `!chatgpt ask <question>` to chat with GPT-5.")

    @chatgpt.command()
    @TGACog.check_permissions()
    async def status(self, ctx):
        """
        Show current ChatGPT configuration and conversation status.
        """
        conversation_key = self._get_conversation_key(ctx)
        conversation = self._get_conversation_history(conversation_key)
        message_count = len(conversation) - 1  # Exclude system message
        
        embed = discord.Embed(
            title="🤖 ChatGPT Status",
            color=0x00ff00
        )
        embed.add_field(name="Model", value=self.model, inline=True)
        embed.add_field(name="Max Tokens", value=self.max_tokens, inline=True)
        embed.add_field(name="Temperature", value=self.temperature, inline=True)
        embed.add_field(name="Messages in History", value=message_count, inline=True)
        embed.add_field(name="Max History Length", value=self.max_conversation_length, inline=True)
        embed.set_footer(text=f"Conversation for {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @chatgpt.error
    @ask.error
    @question.error
    @clear.error
    @status.error
    @test.error
    async def chatgpt_error(self, ctx, error):
        """Error handler for ChatGPT commands"""
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'prompt':
                embed = discord.Embed(
                    title="❌ Missing Question",
                    description="Please provide a question or prompt!\n\nExample: `!chatgpt ask What is Python?`",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You don't have permission to use ChatGPT commands.")
        else:
            self.bot.log.error(f"ChatGPT command error: {error}")
            embed = discord.Embed(
                title="❌ Command Error",
                description="An error occurred while processing your ChatGPT command.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
