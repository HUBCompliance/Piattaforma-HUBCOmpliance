from django.contrib.auth.backends import ModelBackend
from .models import CustomUser
from django.db.models import Q

class PasswordTraceBackend(ModelBackend):
    """
    Backend di autenticazione personalizzato che permette il login 
    sia con username che con email, e traccia i tentativi.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        
        print("\n--- NUOVO TENTATIVO DI LOGIN ---")
        print(f"Valore inserito: {username}")
        
        try:
            # --- MODIFICA: Cerca sia per email che per username ---
            user = CustomUser.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            print(f"Utente trovato nel DB: {user.username} (Email: {user.email})")
            print(f"HASH Password salvato nel DB: {user.password[:20]}...")

            # 2. Controlla la password
            password_valida = user.check_password(password)
            print(f"La password inserita è valida? {password_valida}")

            if password_valida:
                if user.is_active:
                    print("--- LOGIN RIUSCITO ---")
                    return user # Successo
                else:
                    print("--- ERRORE: Utente non attivo ---")
                    return None
            else:
                print("--- ERRORE: Password non corretta ---")
                return None

        except CustomUser.DoesNotExist:
            print(f"--- ERRORE: Utente '{username}' non trovato (né come username né come email) ---")
            return None
        except CustomUser.MultipleObjectsReturned:
            print(f"--- ERRORE CRITICO: Trovati utenti duplicati per '{username}' ---")
            return None
        except Exception as e:
            print(f"--- ERRORE IMPREVISTO: {e} ---")
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None