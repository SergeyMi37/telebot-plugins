reports_command = '/reports'
reports_no_access = "Извините, у вас нет доступа к этой функции."
reports_wrong_format = f'{reports_command} После ключевого слова через пробел нужно ввести параметры отчета.\n' \
                        f'Например\n' \
                        f'<pre>/reports date:today mode:noname labels:Табель</pre>\n' \
                        f'  date:yesterday - отчет за вчера\n' \
                        f'  date:today - отчет за сегодня\n' \
                        f'  date:weekly - отчет за неделю\n' \
                        f'  date:гггг-мм-дд:гггг-мм-дд - отчет за конкретный период\n' \
                        f'  mode:name - включяать в отчет ФИО и дату\n' \
                        f'  mode:txt - вывести отчет в текстовый файл\n' \
                        f'  mode:xlsx - вывести отчет в xlsx файл\n' \
                        f'  labels:Табель,Проект\n\n' \
                        f'Или в другом формате:' \
                        f'  /reports_date_20240815_20240815_mode_noname_labels_tabel_rating\n'
broadcast_command = '/broadcast'
broadcast_no_access = "Sorry, you don't have access to this function."
broadcast_wrong_format = f'To send message to all your users,' \
                         f' type {broadcast_command} command with text separated by space.\n' \
                         f'For example:\n' \
                         f'{broadcast_command} Hello, my users! This <b>bold text</b> is for you, ' \
                         f'as well as this <i>italic text.</i>\n\n' \
                         f'Examples of using <code>HTML</code> style you can found <a href="https://core.telegram.org/bots/api#html-style">here</a>.'
confirm_broadcast = "Confirm ✅"
decline_broadcast = "Decline ❌"
message_is_sent = "Message is sent ✅"
declined_message_broadcasting = "Message broadcasting is declined ❌"
error_with_html = "Can't parse your text in <code>HTML</code> style. Reason: \n{reason}"

