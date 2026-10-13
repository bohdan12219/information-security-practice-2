# Звіт аудиту безпеки — «Електронний деканат»

| Поле | Значення |
|---|---|
| Аудитор | Студент, група КН |
| Дата аудиту | 2026-10-13 |
| Версія системи | commit `final-audit` |
| Обсяг (scope) | API FastAPI, БД SQLite, Docker-образ, Nginx, залежності |
| Поза обсягом | фронтенд, хост-ОС, соціальна інженерія |
| Методи | STRIDE, OWASP Top 10 (2021), Trivy, pip-audit, Bandit, security_check.sh, pentest_mini.sh |

## 1. Резюме для керівництва
Система пройшла комплексне посилення (Field-Level шифрування, сліпі індекси, аудит 5W, блокування Brute Force, HTTPS та non-root контейнер). Критичних архітектурних вразливостей не виявлено. Визначено компроміс блокування за логіном (ризик навмисного блокування користувача) та рекомендовано перехід на асиметричні JWT (RS256) й MFA.

| Критичні | Високі | Середні | Низькі |
|---|---|---|---|
| 0 | 1 | 2 | 1 |

## 2. Інвентаризація активів
| Актив | Тип | Критичність | Обґрунтування |
|---|---|---|---|
| data/app.db | Дані | Критичний | ПІБ, зашифровані email, оцінки |
| ENCRYPTION_KEY, BLIND_INDEX_KEY, JWT_SECRET_KEY | Секрети | Критичний | Компрометація = розшифрування PII або підробка токенів |
| data/backups/*.db.enc | Дані | Високий | Зашифрована копія БД |
| audit_log | Дані | Середній | Журнал подій для розслідування інцидентів |

## 3. Реалізовані шари захисту (Defense in Depth)
| Шар | Механізм | Де (файл / робота) |
|---|---|---|
| Автентифікація | bcrypt, JWT access+refresh | ЗПР-1, `app/security.py`, `app/auth/` |
| Авторизація | RBAC admin/teacher/student | ЗПР-1, `app/auth/dependencies.py` |
| Веб-рівень | Pydantic, bleach, CSP, CORS, slowapi | ЗПР-1, `app/middleware/` |
| Шифрування даних | Fernet для email/phone, сліпий індекс HMAC, зашифрований бекап | ЗПР-2, `app/crypto/`, `scripts/` |
| Аудит і моніторинг | audit_log 5W, детектор Brute Force, security-stats | ЗПР-2, `app/audit/` |
| Середовище | non-root, read-only FS, cap_drop: ALL, Nginx HTTPS | ЗПР-2, Dockerfile, `nginx/` |
| DevSecOps | Trivy, pip-audit, Bandit, security_check.sh | ЗПР-2, `scripts/`, `reports/` |

## 4. Модель загроз STRIDE
| STRIDE | Загроза | Реалізований контрзахід | Залишковий ризик |
|---|---|---|---|
| Spoofing | Підбір пароля викладача; підробка JWT | bcrypt, algorithms=[HS256], slowapi + детектор Brute Force | Немає MFA; симетричний ключ |
| Tampering | Студент змінює оцінку; підміна шифротексту | RBAC require_role, HMAC Fernet | Журнал аудиту в тій самій БД |
| Repudiation | Викладач заперечує виставлену оцінку | assigned_by у моделі Grade, audit_log 5W, data_change | Адмін БД теоретично може модифікувати рядки |
| Information Disclosure | Витік файлу app.db або бекапу | Fernet для email/phone, TLS 1.3, зашифрований бекап | full_name відкритий у БД |
| Denial of Service | Флуд /auth/login | slowapi, Nginx limit_req, client_max_body_size | Навмисне блокування чужого логіну на 5 хв |
| Elevation of Privilege | Студент -> admin; втеча з контейнера | RBAC, non-root appuser, cap_drop: ALL, no-new-privileges | Можливий IDOR у майбутніх ендпоінтах |

## 5. Матриця ризиків (залишковий ризик)
| # | Загроза | Й (1–5) | В (1–5) | Ризик | Рівень | Обґрунтування |
|---|---|---|---|---|---|---|
| R1 | Brute Force | 2 | 3 | 6 | Середній | Детектор блокує після 5 спроб, але немає MFA |
| R2 | SQL Injection | 1 | 5 | 5 | Середній | SQLAlchemy ORM виключає конкатенацію в запитах |
| R3 | Stored XSS | 1 | 4 | 4 | Низький | Bleach та Pydantic валідація очищують коментарі |
| R4 | Крадіжка JWT | 2 | 4 | 8 | Середній | Термін дії access-токена 30 хв; передача лише HTTPS |
| R5 | Витік файлу БД | 1 | 4 | 4 | Низький | PII зашифровано Fernet, бекапи зашифровані |
| R6 | Втрата ENCRYPTION_KEY | 1 | 5 | 5 | Середній | Призведе до втрати даних; потрібен бекап ключів |
| R7 | Вразлива залежність | 3 | 3 | 9 | Середній | Відомі CVE у старих starlette/python-jose |
| R8 | Фішинг викладача | 2 | 4 | 8 | Середній | Людський фактор залишається через відсутність MFA |

## 6. Знахідки та рекомендації
| ID | Рівень | Знахідка | Доказ | Рекомендація | Статус |
|---|---|---|---|---|---|
| F-01 | High | Fallback JWT-секрет у config.py | security_check.sh | Прибрати fallback, впровадити fail-fast | Виправлено |
| F-02 | Medium | Вразливі транзитивні бібліотеки (starlette, ecdsa) | reports/pip-audit.txt | Запланувати оновлення та перехід на PyJWT | Прийнятий ризик |
| F-03 | Low | Відкритий full_name у базі | inspect DB | Якщо вимагає GDPR — зашифрувати через Fernet | План дій |

## 7. Чеклист OWASP Top 10 (2021)
| ID | Категорія | Статус | Доказ / коментар |
|---|---|---|---|
| A01 | Broken Access Control | ✅ | Тести T5–T7 повертають 403; RBAC перевіряється з БД |
| A02 | Cryptographic Failures | ✅ | Fernet для PII, bcrypt для паролів, HTTPS TLS 1.3 |
| A03 | Injection | ✅ | Тест T10 повертає 401; SQLAlchemy параметризація |
| A04 | Insecure Design | ✅ | Описано модель загроз STRIDE і компроміс lockout |
| A05 | Security Misconfiguration | ✅ | Security headers активні, server_tokens off у Nginx |
| A06 | Vulnerable and Outdated Components | ⚠️ | pip-audit фіксує відомі транзитивні пакети (fastapi/starlette) |
| A07 | Identification and Authentication Failures | ✅ | Тест T12 повертає 429; Brute Force блокується |
| A08 | Software and Data Integrity Failures | ✅ | HMAC Fernet перевіряє шифротекст; бекапи верифікуються |
| A09 | Security Logging and Monitoring Failures | ✅ | audit_log фіксує 5W події; /admin/security-stats |
| A10 | SSRF | N/A | Сервер не робить зовнішніх HTTP-запитів на адреси клієнта |

## 8. Результати автоматизованого сканування
| Інструмент | Тип | CRITICAL | HIGH | MEDIUM | Дія |
|---|---|---|---|---|---|
| Trivy | Container SCA | 0 | 0 | 0 | Образ побудовано на python:3.11-slim без root |
| pip-audit | Python SCA | — | Є знахідки | — | Задокументовано в F-02 (прийнятий ризик) |
| Bandit | SAST | — | 0 | 0 | Безпечний код ядра додатку |
| security_check.sh | Конфігурація | 0 | 0 | — | SECURITY CHECK PASSED |

## 9. Результати мінітестів
Усі 12 базових перевірок scripts/pentest_mini.sh успішно пройдені (✅ захищено).

## 10. Моніторинг і KPI
* Показники активності відстежуються через `/admin/security-stats`.
* MTTD склав менше 1 секунди при фіксації 5-ї невдалої спроби.
* MTTR — негайна відповідь 429 при наступному запиті.
* Бекап перевірено утилітою `restore_db.py`.

## 11. План покращень
1. Впровадження FIDO2 / WebAuthn або TOTP MFA для адміністраторів і викладачів.
2. Експорт журналів аудиту на віддалений SIEM/Syslog сервер.
3. Ротація токенів із переходом на асиметричний алгоритм RS256.

## 12. Висновок
Система «Електронний деканат» відповідає вимогам стандарту базової безпеки, містить ешелонований захист і готова до експлуатації за умови контролю фізичного доступу до ключів шифрування.
