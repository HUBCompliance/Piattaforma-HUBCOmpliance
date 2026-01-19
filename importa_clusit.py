import os
import django
import pandas as pd
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from compliance.models import DomandaFornitore

def import_excel():
    files = [f for f in os.listdir('.') if f.startswith('Questionario') and f.endswith('.xlsx')]
    if not files:
        print("Errore: File Excel non trovato!")
        return
    
    file_path = files[0]
    print(f"Analisi file: {file_path}")

    # Carichiamo il foglio 'Questionario' saltando le righe grafiche iniziali
    # L'header reale del CLUSIT è alla riga 1 (indice 0 in pandas se saltiamo il superfluo)
    df = pd.read_excel(file_path, sheet_name='Questionario', header=0)

    # Pulizia nomi colonne: rimuoviamo invii a capo, spazi doppi e rendiamo tutto MAIUSCOLO
    df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
    
    print(f"Colonne rilevate: {df.columns.tolist()[:10]}...")

    # Riempimento celle unite (Sezione, Codice, Tema)
    if 'SEZIONE' in df.columns: df['SEZIONE'] = df['SEZIONE'].ffill()
    if 'CODICE' in df.columns: df['CODICE'] = df['CODICE'].ffill()
    if 'TEMA' in df.columns: df['TEMA'] = df['TEMA'].ffill()

    count = 0
    DomandaFornitore.objects.all().delete()
    
    for index, row in df.iterrows():
        domanda_testo = str(row.get('DOMANDA', '')).strip()
        
        # Salta se la domanda è vuota o è l'intestazione ripetuta
        if not domanda_testo or domanda_testo == 'nan' or domanda_testo == 'DOMANDA':
            continue
            
        # Funzione di utilità per pulire i pesi
        def pulisci_peso(valore):
            try:
                if pd.isna(valore) or str(valore).strip() == '':
                    return 1.0
                return float(valore)
            except:
                return 1.0

        try:
            DomandaFornitore.objects.create(
                sezione=str(row.get('SEZIONE', 'N/D')),
                codice=str(row.get('CODICE', 'N/D')),
                tema=str(row.get('TEMA', 'N/D')),
                domanda=domanda_testo,
                iso_27001=str(row.get('ISO/IEC 27001', '')),
                fncs=str(row.get('FNCS 2.1', '')),
                # Cerchiamo le colonne pesi anche se hanno nomi leggermente diversi
                peso_tema=pulisci_peso(row.get('PESO TEMA', row.get('PESO TEMA SEL', 1.0))),
                peso_domanda=pulisci_peso(row.get('PESO DOMANDA', row.get('PESO DOMANDA SEL', 1.0))),
                tipo_range=str(row.get('RANGE RISPOSTA', 'Range_1'))
            )
            count += 1
        except Exception as e:
            print(f"Salto riga {index} per errore: {e}")
    
    print(f"\n✅ SUCCESSO: {count} domande caricate correttamente!")

if __name__ == "__main__":
    import_excel()
