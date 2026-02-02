"""
Advanced Telegram Bot for Audio Effects
Multiple effects, progress tracking, and queue system
"""
import os
import logging
import asyncio
from datetime import datetime
from collections import deque
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from pydub import AudioSegment
from pydub.effects import low_pass_filter, high_pass_filter, compress_dynamic_range
from pydub.playback import _play_with_simpleaudio

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8178596130:AAFttDeuEkHSFzpBzVg9zTwQbGX4Il0O5zM")
TEMP_DIR = "temp"
MAX_QUEUE_SIZE = 10

# Create temp directory
os.makedirs(TEMP_DIR, exist_ok=True)

# Queue system
user_queues = {}
processing_users = set()


class AudioEffects:
    """Collection of audio effects"""
    
    @staticmethod
    def muffled(audio, intensity="medium"):
        """Make audio sound muffled (through a wall)"""
        cutoffs = {"light": 1500, "medium": 800, "heavy": 400}
        cutoff = cutoffs.get(intensity, 800)
        muffled = low_pass_filter(audio, cutoff)
        return muffled - 3  # Reduce volume slightly
    
    @staticmethod
    def underwater(audio):
        """Underwater effect with bubbling sound"""
        # Heavy low-pass + volume modulation
        underwater = low_pass_filter(audio, 300)
        underwater = underwater - 6  # Quieter
        # Add slight wobble (frequency modulation simulation)
        return underwater
    
    @staticmethod
    def phone(audio):
        """Old telephone/radio effect"""
        # Bandpass filter (remove low and high frequencies)
        phone = high_pass_filter(audio, 300)
        phone = low_pass_filter(phone, 3000)
        # Add compression
        phone = compress_dynamic_range(phone)
        return phone - 2
    
    @staticmethod
    def echo(audio, delay_ms=300, decay=0.5):
        """Add echo effect"""
        # Create delayed copy
        silence = AudioSegment.silent(duration=delay_ms)
        delayed = silence + audio
        # Mix with original
        echo_audio = audio.overlay(delayed - (20 * (1 - decay)))
        return echo_audio
    
    @staticmethod
    def reverb(audio):
        """Simple reverb effect using multiple echoes"""
        reverb_audio = audio
        delays = [50, 100, 150, 200, 250]
        decays = [0.3, 0.25, 0.2, 0.15, 0.1]
        
        for delay, decay in zip(delays, decays):
            silence = AudioSegment.silent(duration=delay)
            delayed = silence + audio
            reverb_audio = reverb_audio.overlay(delayed - (20 / decay))
        
        return reverb_audio
    
    @staticmethod
    def speed_change(audio, speed=1.5):
        """Change playback speed"""
        # Change frame rate to alter speed
        sound_with_altered_frame_rate = audio._spawn(
            audio.raw_data, 
            overrides={"frame_rate": int(audio.frame_rate * speed)}
        )
        return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
    
    @staticmethod
    def pitch_shift(audio, semitones=2):
        """Shift pitch up or down"""
        # Change pitch by altering sample rate
        new_sample_rate = int(audio.frame_rate * (2.0 ** (semitones / 12.0)))
        pitched = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': new_sample_rate}
        )
        return pitched.set_frame_rate(audio.frame_rate)
    
    @staticmethod
    def nightmare(audio):
        """Creepy nightmare effect"""
        # Combine: pitch down + reverb + slow down
        nightmare = AudioEffects.pitch_shift(audio, -5)
        nightmare = AudioEffects.speed_change(nightmare, 0.7)
        nightmare = AudioEffects.reverb(nightmare)
        return nightmare - 3


# Effect presets
EFFECTS = {
    "muffled_light": {"name": "🔇 Muffled (Light)", "func": lambda a: AudioEffects.muffled(a, "light")},
    "muffled_medium": {"name": "🔇 Muffled (Medium)", "func": lambda a: AudioEffects.muffled(a, "medium")},
    "muffled_heavy": {"name": "🔇 Muffled (Heavy)", "func": lambda a: AudioEffects.muffled(a, "heavy")},
    "underwater": {"name": "🌊 Underwater", "func": AudioEffects.underwater},
    "phone": {"name": "📞 Phone/Radio", "func": AudioEffects.phone},
    "echo": {"name": "🔊 Echo", "func": AudioEffects.echo},
    "reverb": {"name": "🎭 Reverb (Hall)", "func": AudioEffects.reverb},
    "speed_fast": {"name": "⚡ Speed Up (1.5x)", "func": lambda a: AudioEffects.speed_change(a, 1.5)},
    "speed_slow": {"name": "🐌 Slow Down (0.7x)", "func": lambda a: AudioEffects.speed_change(a, 0.7)},
    "pitch_up": {"name": "⬆️ Pitch Up", "func": lambda a: AudioEffects.pitch_shift(a, 3)},
    "pitch_down": {"name": "⬇️ Pitch Down", "func": lambda a: AudioEffects.pitch_shift(a, -3)},
    "nightmare": {"name": "👻 Nightmare Mode", "func": AudioEffects.nightmare},
}


def get_effects_keyboard():
    """Create inline keyboard for effect selection"""
    keyboard = []
    effects_list = list(EFFECTS.items())
    
    # Create rows of 2 buttons each
    for i in range(0, len(effects_list), 2):
        row = []
        for j in range(2):
            if i + j < len(effects_list):
                effect_id, effect_data = effects_list[i + j]
                row.append(InlineKeyboardButton(
                    effect_data["name"], 
                    callback_data=f"effect_{effect_id}"
                ))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    message = (
        "🎵 *Welcome to Advanced Audio Effects Bot!* 🎵\n\n"
        "I can apply amazing effects to your audio files:\n\n"
        "🔇 Muffled (Light/Medium/Heavy)\n"
        "🌊 Underwater\n"
        "📞 Phone/Radio\n"
        "🔊 Echo\n"
        "🎭 Reverb\n"
        "⚡ Speed Up/Down\n"
        "⬆️⬇️ Pitch Shift\n"
        "👻 Nightmare Mode\n\n"
        "📤 *How to use:*\n"
        "1. Send me an audio file\n"
        "2. Choose an effect from the menu\n"
        "3. Wait for processing (with live progress!)\n"
        "4. Get your processed audio!\n\n"
        "✨ I can handle multiple files in a queue!"
    )
    await update.message.reply_text(message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    message = (
        "🎵 *Advanced Audio Effects Bot - Help* 🎵\n\n"
        "*Available Effects:*\n\n"
        "🔇 *Muffled* - Sound through a wall (3 intensity levels)\n"
        "🌊 *Underwater* - Deep underwater effect\n"
        "📞 *Phone/Radio* - Old telephone or radio sound\n"
        "🔊 *Echo* - Classic echo effect\n"
        "🎭 *Reverb* - Concert hall reverb\n"
        "⚡ *Speed* - Speed up or slow down\n"
        "⬆️⬇️ *Pitch* - Change pitch higher or lower\n"
        "👻 *Nightmare* - Creepy horror effect\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/queue - Check your queue status\n\n"
        "*Features:*\n"
        "✅ Real-time progress updates\n"
        "✅ Queue system for multiple files\n"
        "✅ Supports: MP3, WAV, OGG, M4A, FLAC\n"
        "✅ Max file size: 20MB\n"
        "✅ Max queue: 10 files"
    )
    await update.message.reply_text(message, parse_mode='Markdown')


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's queue status"""
    user_id = update.effective_user.id
    
    if user_id not in user_queues or not user_queues[user_id]:
        await update.message.reply_text("📭 Your queue is empty!")
        return
    
    queue_size = len(user_queues[user_id])
    is_processing = user_id in processing_users
    
    status = "🔄 *Processing*" if is_processing else "⏸️ *Waiting*"
    message = (
        f"{status}\n\n"
        f"📊 Queue Status:\n"
        f"Files in queue: {queue_size}/{MAX_QUEUE_SIZE}\n"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio file uploads"""
    user_id = update.effective_user.id
    
    try:
        # Get the file
        if update.message.audio:
            file = update.message.audio
        elif update.message.voice:
            file = update.message.voice
        elif update.message.document:
            file = update.message.document
        else:
            await update.message.reply_text("❌ Please send an audio file!")
            return

        # Check file size (20MB limit)
        if file.file_size > 20 * 1024 * 1024:
            await update.message.reply_text("❌ File too large! Maximum size is 20MB.")
            return
        
        # Initialize queue for user if needed
        if user_id not in user_queues:
            user_queues[user_id] = deque()
        
        # Check queue size
        if len(user_queues[user_id]) >= MAX_QUEUE_SIZE:
            await update.message.reply_text(
                f"❌ Queue is full! Maximum {MAX_QUEUE_SIZE} files.\n"
                f"Wait for current files to process."
            )
            return
        
        # Add to queue
        queue_item = {
            'file': file,
            'message_id': update.message.message_id,
            'chat_id': update.effective_chat.id,
            'timestamp': datetime.now()
        }
        user_queues[user_id].append(queue_item)
        
        # Show effect selection menu
        queue_position = len(user_queues[user_id])
        await update.message.reply_text(
            f"✅ Added to queue (Position: {queue_position})\n\n"
            f"🎨 Choose an effect:",
            reply_markup=get_effects_keyboard()
        )
        
        # Store file info in context
        context.user_data[f'file_{update.message.message_id}'] = file
        
    except Exception as e:
        logger.error(f"Error handling audio: {e}", exc_info=True)
        await update.message.reply_text("❌ Error receiving file. Please try again!")


async def handle_effect_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle effect selection from inline keyboard"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    effect_id = query.data.replace("effect_", "")
    
    if effect_id not in EFFECTS:
        await query.edit_message_text("❌ Invalid effect!")
        return
    
    # Check if user has files in queue
    if user_id not in user_queues or not user_queues[user_id]:
        await query.edit_message_text("❌ No files in queue! Send an audio file first.")
        return
    
    # Start processing
    await query.edit_message_text(
        f"🎨 Effect selected: {EFFECTS[effect_id]['name']}\n"
        f"⏳ Starting processing..."
    )
    
    # Process the queue
    asyncio.create_task(process_queue(user_id, effect_id, context, query.message.chat_id))


async def process_queue(user_id, effect_id, context, chat_id):
    """Process user's queue"""
    if user_id in processing_users:
        return  # Already processing
    
    processing_users.add(user_id)
    
    try:
        while user_queues[user_id]:
            queue_item = user_queues[user_id].popleft()
            await process_single_file(user_id, queue_item, effect_id, context, chat_id)
    finally:
        processing_users.discard(user_id)


async def process_single_file(user_id, queue_item, effect_id, context, chat_id):
    """Process a single audio file"""
    file = queue_item['file']
    
    try:
        # Send progress message
        progress_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Processing: 0%\n[          ]"
        )
        
        # Download file
        await update_progress(progress_msg, 10, "Downloading")
        telegram_file = await file.get_file()
        
        input_filename = f"{TEMP_DIR}/input_{user_id}_{file.file_unique_id}.mp3"
        output_filename = f"{TEMP_DIR}/output_{user_id}_{file.file_unique_id}.mp3"
        
        await telegram_file.download_to_drive(input_filename)
        
        # Load audio
        await update_progress(progress_msg, 30, "Loading audio")
        audio = AudioSegment.from_file(input_filename)
        
        # Apply effect
        await update_progress(progress_msg, 50, f"Applying {EFFECTS[effect_id]['name']}")
        processed_audio = EFFECTS[effect_id]['func'](audio)
        
        # Export
        await update_progress(progress_msg, 80, "Exporting")
        processed_audio.export(output_filename, format="mp3", bitrate="192k")
        
        # Upload
        await update_progress(progress_msg, 95, "Uploading")
        
        with open(output_filename, 'rb') as audio_file:
            original_name = getattr(file, 'file_name', 'audio')
            base_name = os.path.splitext(original_name)[0]
            new_name = f"{base_name}_{effect_id}.mp3"
            
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio_file,
                filename=new_name,
                caption=f"✅ Effect applied: {EFFECTS[effect_id]['name']} 🎵"
            )
        
        # Delete progress message
        await progress_msg.delete()
        
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error processing audio. Please try again!"
        )
    finally:
        # Cleanup
        for f in [input_filename, output_filename]:
            if os.path.exists(f):
                os.remove(f)


async def update_progress(message, percent, status):
    """Update progress message"""
    bar_length = 10
    filled = int(bar_length * percent / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    text = f"⏳ {status}: {percent}%\n[{bar}]"
    
    try:
        await message.edit_text(text)
    except:
        pass  # Ignore errors if message wasn't changed


def main():
    """Start the bot"""
    # Check for bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("❌ ERROR: Please set your BOT_TOKEN!")
        print("\nSet environment variable: $env:BOT_TOKEN = \"your_token\"")
        print("Or edit bot_advanced.py line 28")
        return
    
    logger.info("Starting Advanced Audio Effects Bot...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("queue", queue_command))
    app.add_handler(CallbackQueryHandler(handle_effect_selection, pattern="^effect_"))
    app.add_handler(MessageHandler(
        filters.AUDIO | filters.VOICE | filters.Document.AUDIO, 
        handle_audio
    ))
    
    # Start bot
    logger.info("Bot is ready! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
