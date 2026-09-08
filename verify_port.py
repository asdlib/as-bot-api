# -*- coding: utf-8 -*-
u"""Гейт форка: наши исходники обязаны быть апстримом плюс ОДНО переименование.

Зачем это вообще нужно
----------------------
Репа `asdlib/as-bot-api` — снимок без истории апстрима (весь код пришёл одним
коммитом «Release 0.1.0»). Из-за этого нельзя ни спросить `git log`, что у нас
своё, ни перенести форк на новую версию черри-пиком: отделить наши правки от
чужих можно только сравнением с апстримом.

08.09.2026 сравнение было сделано, и выяснилось, что своих правок в исходниках
НЕТ ВООБЩЕ. Все 19 файлов побайтово совпадают с `tdlib/telegram-bot-api`, если
отменить сплошную замену `telegram-bot-api/` -> `as-bot-api/`. Форк — это
переименование каталога, подмена сабмодуля `td` -> `adlib` и имена в CMake.

Отсюда правило, которое этот скрипт и держит: **переход на новую версию Bot API
= копирование апстримных исходников с той же заменой, и ничего больше.** Если
однажды понадобится настоящая правка в C++, скрипт станет красным — и это
верно: такую правку надо вносить осознанно и вписывать сюда исключением, а не
обнаруживать через полгода при следующем переносе.

Как запускать
-------------
    python verify_port.py [путь-к-клону-tdlib/telegram-bot-api]

Клон нужен свой, потому что сравнивать надо с апстримом, а не с константой:

    git clone --filter=blob:none https://github.com/tdlib/telegram-bot-api.git

🚨 Версию апстрима нельзя выбирать на глаз. Апстрим пинит `td` сабмодулем, и
пара «версия bot-api <-> версия td» жёсткая: сборка 1672 упала 92 ошибками
компиляции ровно потому, что исходники 9.6 собирали против td 1.8.67. Ревизия
ниже выбрана так, чтобы её сабмодуль `td` совпадал с базой нашей ветки `adlib`.
"""
import io
import os
import subprocess
import sys

NL = chr(10)

#: Ревизия апстрима, с которой снят порт. Её сабмодуль td = bc9c263e2
#: («Update version to 1.8.67»), а наша ветка adlib/layer229 стоит на потомке
#: этого коммита — значит библиотека не старее той, под которую писан код.
UPSTREAM_REF = '2efabc722'          # «Update version to 10.3», 24.08.2026
UPSTREAM_TD = 'bc9c263e2'

#: Единственное преобразование, которым наш форк отличается от апстрима.
RENAMES_SOURCES = [('as-bot-api/', 'telegram-bot-api/')]
RENAMES_CMAKE = [
    ('AsBotApi', 'TelegramBotApi'),
    ('AS_BOT_API', 'TELEGRAM_BOT_API'),
    ('as-bot-api', 'telegram-bot-api'),
    ('add_subdirectory(adlib', 'add_subdirectory(td'),
    ('SOURCE_DIR}/adlib/CMake', 'SOURCE_DIR}/td/CMake'),
]

HERE = os.path.dirname(os.path.abspath(__file__))


def upstream_show(repo, path):
    p = subprocess.run(['git', 'show', UPSTREAM_REF + ':' + path],
                       cwd=repo, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout.decode('utf-8')


def unrename(text, table):
    for ours, theirs in table:
        text = text.replace(ours, theirs)
    #: CRLF в рабочем дереве на Windows — не различие, а настройка checkout.
    return text.replace(chr(13), '')


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('UPSTREAM_BOTAPI')
    if not repo or not os.path.isdir(os.path.join(repo, '.git')):
        sys.exit('укажите клон tdlib/telegram-bot-api первым аргументом '
                 'или в UPSTREAM_BOTAPI')

    listing = subprocess.run(
        ['git', 'ls-tree', UPSTREAM_REF, '--name-only', 'telegram-bot-api/'],
        cwd=repo, capture_output=True, text=True)
    names = [l.split('/')[-1] for l in listing.stdout.strip().split(NL) if l]
    if not names:
        sys.exit('в апстриме на %s нет telegram-bot-api/ — не та ревизия '
                 'или клон без объектов' % UPSTREAM_REF)

    problems = []

    ours_dir = os.path.join(HERE, 'as-bot-api')
    have = sorted(f for f in os.listdir(ours_dir) if f.endswith(('.cpp', '.h')))
    if have != sorted(names):
        problems.append('состав файлов разошёлся: у нас %d, у апстрима %d'
                        % (len(have), len(names)))

    for n in names:
        theirs = upstream_show(repo, 'telegram-bot-api/' + n)
        path = os.path.join(ours_dir, n)
        if not os.path.exists(path):
            problems.append('%s: нет у нас' % n)
            continue
        ours = io.open(path, encoding='utf-8', newline='').read()
        if unrename(ours, RENAMES_SOURCES) != theirs:
            problems.append('%s: расходится с апстримом не только '
                            'переименованием' % n)

    theirs = upstream_show(repo, 'CMakeLists.txt')
    ours = io.open(os.path.join(HERE, 'CMakeLists.txt'),
                   encoding='utf-8', newline='').read()
    got = unrename(ours, RENAMES_CMAKE)
    if got != theirs:
        problems.append('CMakeLists.txt: расходится сверх наших замен')

    print('апстрим %s (его сабмодуль td: %s)' % (UPSTREAM_REF, UPSTREAM_TD))
    print('сверено исходников: %d' % len(names))
    if problems:
        print(NL + 'ФОРК БОЛЬШЕ НЕ ЧИСТОЕ ПЕРЕИМЕНОВАНИЕ (%d):' % len(problems))
        for p in problems:
            print('  ' + p)
        print(NL + 'Либо правка внесена случайно — откатите её; либо осознанно —')
        print('тогда впишите её сюда исключением и объясните, ЧЕМ она')
        print('оправдана: следующий перенос версии её иначе молча потеряет.')
        return 1
    print('OK: форк = апстрим + переименование, своих правок в C++ нет')
    return 0


if __name__ == '__main__':
    sys.exit(main())
