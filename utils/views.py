import discord


class Confirm(discord.ui.View):
    def __init__(self, user_id=None, timeout=180.0):
        super().__init__(timeout=timeout)
        self.value = None
        self.user_id = user_id

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.label = "Confirmed"
        for elem in button.view.children:
            elem.style = discord.ButtonStyle.grey
            elem.disabled = True
        button.style = discord.ButtonStyle.green
        await interaction.message.edit(view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, emoji="❌")
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.label = "Cancelled"
        for elem in button.view.children:
            elem.style = discord.ButtonStyle.grey
            elem.disabled = True
        button.style = discord.ButtonStyle.red
        await interaction.message.edit(view=None)
        self.value = False
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_id is not None:
            return interaction.user.id == self.user_id
        return True


class Paginator(discord.ui.View):
    def __init__(self, pages):
        super().__init__()
        self.curr_index = 0
        self.pages = pages

    @discord.ui.button(label='First Page', style=discord.ButtonStyle.blurple, emoji="⏮️")
    async def first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.curr_index == 0:
            return
        self.curr_index = 0
        await interaction.message.edit(embed=self.pages[self.curr_index], view=self)

    @discord.ui.button(label='Prev. Page', style=discord.ButtonStyle.blurple, emoji="◀️")
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.curr_index == 0:
            return
        self.curr_index -= 1
        await interaction.message.edit(embed=self.pages[self.curr_index], view=self)

    @discord.ui.button(label='Next Page', style=discord.ButtonStyle.blurple, emoji="▶️")
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.curr_index == len(self.pages) - 1:
            return
        self.curr_index += 1
        await interaction.message.edit(embed=self.pages[self.curr_index], view=self)

    @discord.ui.button(label='Last Page', style=discord.ButtonStyle.blurple, emoji="⏭️")
    async def last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.curr_index == len(self.pages) - 1:
            return
        self.curr_index = len(self.pages) - 1
        await interaction.message.edit(embed=self.pages[self.curr_index], view=self)


class Options(discord.ui.View):
    def __init__(self, options, min_values=1, max_values=1):
        super().__init__()
        self.dropdown = self.Dropdown(
            options, min_values=min_values, max_values=max_values)
        self.dropdown.callback = self.select_callback
        self.add_item(self.dropdown)

    class Dropdown(discord.ui.Select):
        def __init__(self, options, min_values, max_values):
            super().__init__(placeholder='Select your choice(s)',
                             min_values=min_values, max_values=max_values)
            for option in options:
                self.add_option(label=option['label'][:90], emoji=option['emoji'],
                                value=option['value'], description=option['description'][:50])
            return

    async def select_callback(self, interaction: discord.Interaction):
        self.stop()
