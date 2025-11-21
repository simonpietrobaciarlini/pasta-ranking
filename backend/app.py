from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Permette richieste dal frontend

# IMPORTANTE: Metti la password in una variabile d'ambiente per sicurezza
# Oppure usa un file .env con python-dotenv
CONN_STR = os.getenv(
    'DATABASE_URL',
    "postgresql://neondb_owner:npg_JPUGMQrXe95Z@ep-tiny-darkness-ad2el2sn-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

@app.route('/api/save-ranking', methods=['POST'])
def save_ranking():
    try:
        data = request.json
        print("📥 Dati ricevuti:", data)  # Debug
        
        # Validazione dati
        required_fields = ['nome', 'sesso', 'anno_di_nascita', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo mancante: {field}'}), 400
        
        # Prepara i dati con valori default per paste mancanti
        pastas = ['amatriciana', 'carbonara', 'vongole', 'gricia',
                 'norma', 'pesto', 'cacio_e_pepe', 'ragu_alla_bolognese']
        
        for pasta in pastas:
            if pasta not in data:
                data[pasta] = None  # Imposta NULL se mancante
        
        # Salva nella tabella wide (questionario_pasta)
        with psycopg.connect(CONN_STR) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO questionario_pasta (
                        nome, sesso, anno_di_nascita, data,
                        amatriciana, carbonara, vongole, gricia,
                        norma, pesto, cacio_e_pepe, ragu_alla_bolognese
                    )
                    VALUES (%(nome)s, %(sesso)s, %(anno_di_nascita)s, %(data)s,
                            %(amatriciana)s, %(carbonara)s, %(vongole)s, %(gricia)s,
                            %(norma)s, %(pesto)s, %(cacio_e_pepe)s, %(ragu_alla_bolognese)s)
                    RETURNING id;
                    """,
                    data
                )
                new_id = cur.fetchone()[0]
                
                # Salva anche nella tabella narrow (pasta_narrow)
                pastas = ['amatriciana', 'carbonara', 'vongole', 'gricia',
                         'norma', 'pesto', 'cacio_e_pepe', 'ragu_alla_bolognese']
                
                new_ids = []
                for pasta in pastas:
                    if pasta in data:
                        cur.execute(
                            """
                            INSERT INTO pasta_narrow (
                                nome, sesso, anno_di_nascita, data,
                                row, ranking
                            )
                            VALUES (
                                %(nome)s, %(sesso)s, %(anno_di_nascita)s, %(data)s,
                                %(pasta)s, %(ranking)s
                            )
                            RETURNING id;
                            """,
                            {
                                'nome': data['nome'],
                                'sesso': data['sesso'],
                                'anno_di_nascita': data['anno_di_nascita'],
                                'data': data['data'],
                                'pasta': pasta,
                                'ranking': data[pasta]
                            }
                        )
                        narrow_id = cur.fetchone()[0]
                        new_ids.append(narrow_id)
                
                return jsonify({
                    'success': True,
                    'id': new_id,
                    'narrow_ids': new_ids,
                    'message': 'Dati salvati con successo!'
                }), 201
                
    except psycopg.Error as e:
        print(f"Errore database: {e}")
        return jsonify({'error': 'Errore nel salvataggio dei dati'}), 500
    except Exception as e:
        print(f"Errore generico: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint per verificare che il server funzioni"""
    return jsonify({'status': 'ok', 'message': 'Server attivo'}), 200

@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Endpoint per testare la connessione al database"""
    try:
        with psycopg.connect(CONN_STR) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                return jsonify({
                    'success': True,
                    'database_version': version
                }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)