command_start = '/stats'
only_for_admins = 'Извините, эта функция доступна только для администраторов. Установите флаг "admin" в панели администратора django.'
secret_admin_commands = f"⚠️ Secret Admin commands\n" \
                        f"{command_start} - bot stats"

users_amount_stat = "<b>Users</b>: {user_count}\n" \
                    "<b>24h active</b>: {active_24}"
BR = chr(13)+chr(10)