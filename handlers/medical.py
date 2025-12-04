from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from services.medical_service import (
    update_employee_medical_info, 
    get_employee_status, 
    get_all_medical_issues, 
    load_medical_data,
    is_manager,
    add_employee,
    remove_employee,
    get_all_roles
)
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Conversation states
SELECT_EMPLOYEE, SELECT_TYPE, INPUT_DATE = range(3)

# Add employee states
ADD_INPUT_NAME, ADD_SELECT_ROLE = range(10, 12)

# Remove employee states
REMOVE_SELECT_EMPLOYEE, REMOVE_CONFIRM = range(20, 22)

ADMIN_SURNAMES = ["мишра", "анубхав", "ахмитенко", "смолкина", "лемехова"]

def get_user_surname(user_id):
    users_file = 'data/users.json'
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users_db = json.load(f)
                user_data = users_db.get(str(user_id))
                if isinstance(user_data, dict):
                    return user_data.get('surname', '').lower()
                elif isinstance(user_data, str):
                    return user_data.lower()
        except Exception:
            pass
    return ""

def check_permissions(user_id):
    surname = get_user_surname(user_id)
    
    # Check hardcoded admins
    for admin_name in ADMIN_SURNAMES:
        if admin_name in surname:
            return True, surname
            
    # Check manager role
    if is_manager(surname):
        return True, surname
        
    return False, surname

async def medical_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the Medical Commission tab"""
    user = update.effective_user
    is_allowed, surname = check_permissions(user.id)
    
    keyboard = [
        [InlineKeyboardButton("📋 Список всех", callback_data="med_view_all")],
        [InlineKeyboardButton("⚠️ Просроченные", callback_data="med_view_expiring")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="med_main_menu")]
    ]
    
    if is_allowed:
        keyboard.append([InlineKeyboardButton("✏️ Редактировать", callback_data="med_edit_start")])
        keyboard.append([InlineKeyboardButton("➕ Добавить сотрудника", callback_data="med_add_start")])
        keyboard.append([InlineKeyboardButton("➖ Удалить сотрудника", callback_data="med_remove_start")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🏥 <b>Медицинская комиссия</b>\nВыберите действие:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def medical_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    if query.data == "med_view_all":
        data = load_medical_data()
        employees = data.get('employees', [])
        
        if not employees:
            await query.edit_message_text("Список сотрудников пуст.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="med_menu")]]))
            return

        # Sort by role priority then name
        ROLE_PRIORITY = {
            'manager': 0,
            'mentor': 1,
            'instructor': 2,
            'universal': 3,
            'pizzamaker': 4,
            'cashier': 5,
            'courier': 6,
            'trainee': 7
        }
        
        employees.sort(key=lambda x: (ROLE_PRIORITY.get(x.get('role', ''), 99), x['name']))
        
        msg = "📋 <b>Список сотрудников:</b>\n\n"
        
        ROLE_TRANSLATIONS = {
            'manager': 'Менеджер',
            'mentor': 'Наставник',
            'instructor': 'Инструктор',
            'universal': 'Универсал',
            'pizzamaker': 'Пиццамейкер',
            'cashier': 'Кассир',
            'courier': 'Курьер',
            'trainee': 'Стажёр'
        }
        
        for emp in employees:
            status_icon = "✅"
            if emp.get('status') == 'missing_docs':
                status_icon = "❌"
            
            role = emp.get('role', 'N/A')
            # Map roles to icons
            role_icons = {
                'manager': '💼',
                'pizzamaker': '🍕',
                'cashier': '💰',
                'courier': '🚗',
                'universal': '🌟',
                'mentor': '🎓',
                'instructor': '📚'
            }
            role_icon = role_icons.get(role, '👤')
            role_ru = ROLE_TRANSLATIONS.get(role, role)
            
            name = emp['name']
            
            line = f"{status_icon} <b>{name}</b> <i>({role_icon} {role_ru})</i>\n"
            if emp.get('status') == 'missing_docs':
                line += "   ⚠️ <i>Нет документов</i>\n"
            else:
                med = emp.get('med_commission_date', '—')
                san = emp.get('san_min_date', '—')
                line += f"   Комиссия: <code>{med}</code>\n"
                line += f"   Сан.минимум: <code>{san}</code>\n"
            
            line += "\n" # Add space between entries
            
            if len(msg) + len(line) > 4000:
                msg += "...\n(Список обрезан)"
                break
            msg += line
            
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="med_menu")]]
        
        try:
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error displaying medical list: {e}")
            await query.edit_message_text("❌ Ошибка при отображении списка. Попробуйте позже.", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "med_view_expiring":
        issues = get_all_medical_issues()
        
        if not issues:
            await query.edit_message_text("✅ Все документы в порядке! Проблем не найдено.", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="med_menu")]]))
            return
            
        msg = "⚠️ <b>Проблемные документы:</b>\n\n"
        for item in issues:
            icon = "🔴" if "Просрочено" in item['issue'] or "Нет документов" in item['issue'] else "🟡"
            
            # Extract deadline info if present in details
            details = item['details']
            
            line = f"{icon} <b>{item['name']}</b>\n"
            line += f"   └ <i>{item['issue']}</i>\n"
            line += f"      📅 {details}\n\n"
            
            if len(msg) + len(line) > 4000:
                msg += "...\n(Список обрезан)"
                break
            msg += line
            
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="med_menu")]]
        try:
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error displaying expiring list: {e}")
            await query.edit_message_text("❌ Ошибка при отображении списка. Попробуйте позже.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "med_menu":
        await medical_menu(update, context)

    elif query.data == "med_main_menu":
        # Return to main menu
        await query.edit_message_text("Возвращаюсь в главное меню...")
        from handlers.start import show_menu
        await show_menu(update, context)

# --- Edit Flow ---

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    # Double check permissions
    is_allowed, _ = check_permissions(update.effective_user.id)
    if not is_allowed:
        await query.edit_message_text("⛔️ У вас нет прав на редактирование.")
        return ConversationHandler.END
        
    data = load_medical_data()
    employees = data.get('employees', [])
    employees.sort(key=lambda x: x['name'])
    
    keyboard = []
    row = []
    for emp in employees:
        row.append(InlineKeyboardButton(emp['name'], callback_data=f"edit_emp_{emp['name']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel_edit")])
    
    await query.edit_message_text("Выберите сотрудника для редактирования:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_EMPLOYEE

async def select_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    data = query.data
    if data == "cancel_edit":
        await medical_menu(update, context)
        return ConversationHandler.END
        
    if not data.startswith("edit_emp_"):
        return SELECT_EMPLOYEE
        
    employee_name = data[9:]
    context.user_data['edit_emp_name'] = employee_name
    
    keyboard = [
        [InlineKeyboardButton("Мед. комиссия", callback_data="type_med")],
        [InlineKeyboardButton("Сан. минимум", callback_data="type_san")],
        [InlineKeyboardButton("🔙 Отмена", callback_data="cancel_edit")]
    ]
    
    await query.edit_message_text(f"Редактирование: <b>{employee_name}</b>\nЧто обновляем?", 
                                reply_markup=InlineKeyboardMarkup(keyboard),
                                parse_mode='HTML')
    return SELECT_TYPE

async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    data = query.data
    if data == "cancel_edit":
        await medical_menu(update, context)
        return ConversationHandler.END
        
    if data == "type_med":
        context.user_data['edit_type'] = 'med'
        type_name = "Мед. комиссию"
    elif data == "type_san":
        context.user_data['edit_type'] = 'san'
        type_name = "Сан. минимум"
    else:
        return SELECT_TYPE
    
    # Add cancel button during date input
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_date_input")]]
    await query.edit_message_text(
        f"Введите новую дату для <b>{type_name}</b> в формате DD.MM.YYYY:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return INPUT_DATE

async def cancel_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel button during date input"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    await query.edit_message_text("❌ Редактирование отменено.")
    # Give a moment before showing menu
    import asyncio
    await asyncio.sleep(0.5)
    # Create a new message for the menu instead of editing
    await query.message.reply_text("Возвращаюсь в меню...")
    # Show menu in new message
    from telegram import Update as FreshUpdate
    fresh_update = FreshUpdate(update.update_id, message=query.message)
    await medical_menu(fresh_update, context)
    return ConversationHandler.END

async def input_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    try:
        datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_date_input")]]
        await update.message.reply_text(
            "❌ Неверный формат. Пожалуйста, введите дату в формате DD.MM.YYYY (например, 25.12.2026):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return INPUT_DATE
        
    name = context.user_data['edit_emp_name']
    edit_type = context.user_data['edit_type']
    
    med_date = text if edit_type == 'med' else None
    san_date = text if edit_type == 'san' else None
    
    success = update_employee_medical_info(name, med_date, san_date)
    
    if success:
        await update.message.reply_text(f"✅ Данные для <b>{name}</b> успешно обновлены!", parse_mode='HTML')
    else:
        await update.message.reply_text(f"❌ Ошибка при обновлении данных для <b>{name}</b>.", parse_mode='HTML')
    
    # Clear user data
    context.user_data.clear()
    
    # Show menu in a new message to ensure buttons work
    from telegram import Update as FreshUpdate
    fresh_update = FreshUpdate(update.update_id, message=update.message)
    await medical_menu(fresh_update, context)
    return ConversationHandler.END

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Редактирование отменено.")
    # Show menu in new message
    from telegram import Update as FreshUpdate
    fresh_update = FreshUpdate(update.update_id, message=update.message)
    await medical_menu(fresh_update, context)
    return ConversationHandler.END

# Handlers definition
medical_menu_handler = MessageHandler(filters.Regex("^🏥 Мед. комиссия$"), medical_menu)

medical_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_edit, pattern="^med_edit_start$")],
    states={
        SELECT_EMPLOYEE: [CallbackQueryHandler(select_employee)],
        SELECT_TYPE: [CallbackQueryHandler(select_type)],
        INPUT_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_date),
            CallbackQueryHandler(cancel_date_input, pattern="^cancel_date_input$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(select_employee, pattern="^cancel_edit$"),
        CallbackQueryHandler(cancel_date_input, pattern="^cancel_date_input$"),
        CommandHandler("cancel", cancel_edit)
    ]
)

# --- Add Employee Flow ---

async def start_add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    is_allowed, _ = check_permissions(update.effective_user.id)
    if not is_allowed:
        await query.edit_message_text("⛔️ У вас нет прав на добавление сотрудников.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_add")]]
    await query.edit_message_text(
        "➕ <b>Добавление сотрудника</b>\n\nВведите фамилию нового сотрудника:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return ADD_INPUT_NAME

async def add_employee_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    
    if len(name) < 2:
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_add")]]
        await update.message.reply_text(
            "❌ Фамилия слишком короткая. Введите корректную фамилию:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADD_INPUT_NAME
    
    # Capitalize first letter
    name = name.capitalize()
    context.user_data['new_emp_name'] = name
    
    roles = get_all_roles()
    keyboard = []
    row = []
    for role_key, role_name in roles.items():
        row.append(InlineKeyboardButton(role_name, callback_data=f"add_role_{role_key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_add")])
    
    await update.message.reply_text(
        f"Сотрудник: <b>{name}</b>\n\nВыберите должность:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return ADD_SELECT_ROLE

async def add_employee_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    data = query.data
    if data == "cancel_add":
        await query.edit_message_text("❌ Добавление отменено.")
        await medical_menu(update, context)
        return ConversationHandler.END
    
    if not data.startswith("add_role_"):
        return ADD_SELECT_ROLE
    
    role = data[9:]  # Remove "add_role_" prefix
    name = context.user_data.get('new_emp_name')
    
    success, message = add_employee(name, role)
    
    roles = get_all_roles()
    role_name = roles.get(role, role)
    
    if success:
        await query.edit_message_text(
            f"✅ Сотрудник <b>{name}</b> ({role_name}) успешно добавлен!\n\n"
            f"⚠️ Статус: <i>Нет документов</i>\n"
            f"Отредактируйте даты мед. комиссии и сан. минимума.",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(f"❌ {message}", parse_mode='HTML')
    
    context.user_data.clear()
    
    # Show menu
    import asyncio
    await asyncio.sleep(0.5)
    await query.message.reply_text("Возвращаюсь в меню...")
    from telegram import Update as FreshUpdate
    fresh_update = FreshUpdate(update.update_id, message=query.message)
    await medical_menu(fresh_update, context)
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    await query.edit_message_text("❌ Добавление отменено.")
    context.user_data.clear()
    await medical_menu(update, context)
    return ConversationHandler.END

add_employee_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add_employee, pattern="^med_add_start$")],
    states={
        ADD_INPUT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_employee_name),
            CallbackQueryHandler(cancel_add, pattern="^cancel_add$")
        ],
        ADD_SELECT_ROLE: [CallbackQueryHandler(add_employee_role)]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_add, pattern="^cancel_add$"),
        CommandHandler("cancel", lambda u, c: cancel_add(u, c))
    ]
)

# --- Remove Employee Flow ---

async def start_remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    is_allowed, _ = check_permissions(update.effective_user.id)
    if not is_allowed:
        await query.edit_message_text("⛔️ У вас нет прав на удаление сотрудников.")
        return ConversationHandler.END
    
    data = load_medical_data()
    employees = data.get('employees', [])
    employees.sort(key=lambda x: x['name'])
    
    keyboard = []
    row = []
    for emp in employees:
        row.append(InlineKeyboardButton(emp['name'], callback_data=f"remove_emp_{emp['name']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel_remove")])
    
    await query.edit_message_text(
        "➖ <b>Удаление сотрудника</b>\n\nВыберите сотрудника для удаления:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return REMOVE_SELECT_EMPLOYEE

async def select_employee_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    data = query.data
    if data == "cancel_remove":
        await query.edit_message_text("❌ Удаление отменено.")
        await medical_menu(update, context)
        return ConversationHandler.END
    
    if not data.startswith("remove_emp_"):
        return REMOVE_SELECT_EMPLOYEE
    
    employee_name = data[11:]  # Remove "remove_emp_" prefix
    context.user_data['remove_emp_name'] = employee_name
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data="confirm_remove")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_remove")]
    ]
    
    await query.edit_message_text(
        f"⚠️ Вы уверены, что хотите удалить сотрудника <b>{employee_name}</b>?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return REMOVE_CONFIRM

async def confirm_remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    data = query.data
    if data == "cancel_remove":
        await query.edit_message_text("❌ Удаление отменено.")
        context.user_data.clear()
        await medical_menu(update, context)
        return ConversationHandler.END
    
    if data == "confirm_remove":
        name = context.user_data.get('remove_emp_name')
        success, message = remove_employee(name)
        
        if success:
            await query.edit_message_text(f"✅ Сотрудник <b>{name}</b> успешно удалён!", parse_mode='HTML')
        else:
            await query.edit_message_text(f"❌ {message}", parse_mode='HTML')
        
        context.user_data.clear()
        
        import asyncio
        await asyncio.sleep(0.5)
        await query.message.reply_text("Возвращаюсь в меню...")
        from telegram import Update as FreshUpdate
        fresh_update = FreshUpdate(update.update_id, message=query.message)
        await medical_menu(fresh_update, context)
        return ConversationHandler.END
    
    return REMOVE_CONFIRM

async def cancel_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")
    
    await query.edit_message_text("❌ Удаление отменено.")
    context.user_data.clear()
    await medical_menu(update, context)
    return ConversationHandler.END

remove_employee_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_remove_employee, pattern="^med_remove_start$")],
    states={
        REMOVE_SELECT_EMPLOYEE: [CallbackQueryHandler(select_employee_to_remove)],
        REMOVE_CONFIRM: [CallbackQueryHandler(confirm_remove_employee)]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_remove, pattern="^cancel_remove$"),
        CommandHandler("cancel", lambda u, c: cancel_remove(u, c))
    ]
)

medical_handlers = [
    medical_menu_handler,
    medical_conv_handler,
    add_employee_conv_handler,
    remove_employee_conv_handler,
    CallbackQueryHandler(medical_button_handler, pattern="^med_")
]

