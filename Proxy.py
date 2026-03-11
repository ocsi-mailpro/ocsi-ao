"""
Proxy BOAMP - Contourne le CORS
=================================

Installation:
pip install flask flask-cors requests

Lancement:
python proxy.py

Ensuite ouvre: http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# API BOAMP v2.1
BOAMP_API = 'https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records'

@app.route('/')
def index():
    """Sert le fichier index.html"""
    return send_from_directory('.', 'index.html')

@app.route('/api/ao')
def get_ao():
    """Proxy pour l'API BOAMP - contourne le CORS"""
    try:
        # Récupérer les paramètres depuis le frontend
        search = request.args.get('search', '')
        dept = request.args.get('dept', '')
        min_budget = request.args.get('min', 0)
        max_budget = request.args.get('max', 999999999)
        
        # Construire la requête WHERE
        where = 'objet LIKE "informatique" OR objet LIKE "IT" OR objet LIKE "cloud" OR objet LIKE "logiciel" OR objet LIKE "software"'
        
        if search:
            where = f'objet LIKE "{search}" OR descriptionlots LIKE "{search}"'
        
        if dept:
            where += f' AND departement="{dept}"'
        
        # Paramètres pour l'API BOAMP
        params = {
            'where': where,
            'limit': 100,
            'offset': 0,
            'timezone': 'Europe/Paris'
        }
        
        print(f"🔍 Requête BOAMP: {where}")
        
        # Faire la requête à l'API BOAMP
        response = requests.get(BOAMP_API, params=params, timeout=30)
        
        if response.status_code != 200:
            return jsonify({
                'error': True,
                'message': f'Erreur API BOAMP: HTTP {response.status_code}'
            }), 500
        
        data = response.json()
        
        # Transformer les données
        results = []
        for record in data.get('results', []):
            fields = record.get('record', {}).get('fields', {})
            
            # Extraire le budget
            budget = 0
            try:
                montant = fields.get('montant') or fields.get('valeurestimee') or fields.get('montantmarche')
                if montant:
                    budget = int(float(str(montant).replace(' ', '').replace(',', '.')))
            except:
                pass
            
            # Filtrer par budget
            if budget < int(min_budget) or budget > int(max_budget):
                continue
            
            results.append({
                'id': fields.get('idweb', record.get('record', {}).get('id', 'N/A')),
                'title': fields.get('objet', 'Sans titre'),
                'client': fields.get('denominationsociale') or fields.get('nomentite') or fields.get('denomination') or 'Non spécifié',
                'budget': budget,
                'deadline': fields.get('datelimitereponse', 'N/A'),
                'location': (fields.get('departement', 'France') + (' - ' + fields.get('commune', '') if fields.get('commune') else '')).strip(' - '),
                'description': (fields.get('descriptionlots') or fields.get('objetmarche') or fields.get('objet') or '')[:300],
                'url': f"https://www.boamp.fr/avis/detail/{fields.get('idweb', record.get('record', {}).get('id', ''))}",
                'source': 'BOAMP',
                'publishDate': fields.get('dateparution', '')
            })
        
        print(f"✅ {len(results)} AO trouvés")
        
        return jsonify({
            'total': len(results),
            'results': results
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'error': True,
            'message': 'Timeout - l\'API BOAMP est trop lente'
        }), 504
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500

@app.route('/api/status')
def status():
    """Status du proxy"""
    return jsonify({
        'status': 'online',
        'boamp_api': BOAMP_API,
        'cors': 'enabled'
    })

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════╗
    ║     Proxy BOAMP - AOFinder v1.0        ║
    ╚════════════════════════════════════════╝
    
    🚀 Serveur démarré !
    
    📡 Ouvre dans ton navigateur:
       http://localhost:5000
    
    ✅ CORS activé - contournement réussi
    
    Ctrl+C pour arrêter
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
