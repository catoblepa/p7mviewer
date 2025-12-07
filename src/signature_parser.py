#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Davide Truffa <davide@catoblepa.org>

from asn1crypto import cms, x509
import sys
import base64
from datetime import datetime
import gettext
import os

# Setup gettext per localizzazione
APP_ID = 'io.github.catoblepa.p7mviewer'
# Use system locale directory for Flatpak, fallback to local for development
if os.path.exists('/app/share/locale'):
    LOCALE_DIR = '/app/share/locale'
else:
    LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locale')
gettext.bindtextdomain(APP_ID, LOCALE_DIR)
gettext.textdomain(APP_ID)
_ = gettext.gettext

def rileva_formato_p7m(data):
    """
    Detect if the P7M file is in Base64, DER or PEM format.
    Returns: ('base64', decoded_data) or ('der', data) or ('pem', data)
    """
    # Check if it's Base64
    try:
        # Remove whitespace and newlines
        data_clean = data.strip()
        if isinstance(data_clean, bytes):
            data_clean = data_clean.decode('ascii', errors='ignore').strip()
        # Try to decode from base64
        decoded = base64.b64decode(data_clean)
        # Verify that the decoded data is valid by re-encoding it
        reencoded = base64.b64encode(decoded).decode('ascii').strip()
        if reencoded.replace('\n', '').replace('\r', '') == data_clean.replace('\n', '').replace('\r', ''):
            return ('base64', decoded)
    except Exception:
        pass
    
    # If it's not base64, it's probably DER or PEM
    if isinstance(data, bytes):
        # Check if it starts with PEM header
        if b'-----BEGIN' in data[:100]:
            return ('pem', data)
        else:
            return ('der', data)
    return ('der', data)

def estrai_certificati(signed_data):
    certs = []
    if 'certificates' in signed_data and signed_data['certificates'] is not None:
        for cert in signed_data['certificates']:
            if cert.name == 'certificate':
                certs.append(cert.chosen)
    return certs

def cerca_certificato_per_serial(cert_list, serial):
    for cert in cert_list:
        if cert.serial_number == serial:
            return cert
    return None

def estrai_nome_cognome(subject):
    """
    Extract the full name from the certificate subject.
    """
    cn = subject.native.get('common_name', '')
    gn = subject.native.get('given_name', '')
    sn = subject.native.get('surname', '')
    if gn and sn:
        return f"{gn} {sn}"
    return cn

def estrai_codice_fiscale(subject):
    """
    Extract the Tax Code from the certificate subject.
    """
    # Try serial_number
    cf = subject.native.get('serial_number', '')
    if cf:
        # Remove prefixes like 'TINIT-' or similar
        if ':' in cf:
            cf = cf.split(':')[-1]
        return cf
    # Fallback to dn_qualifier
    return subject.native.get('dn_qualifier', '')

def estrai_organization(subject):
    """
    Extract the organization from the certificate subject.
    """
    org = subject.native.get('organization_name', '')
    if not org:
        org = subject.native.get('organizational_unit_name', '')
    return org if org else _('Not present')

def mostra_info_firma(signer, cert_list):
    """
    Extract and return signer information as a dictionary.
    """
    info = {}
    sid = signer['sid']
    serial = None
    if sid.name == 'issuer_and_serial_number':
        serial = sid.chosen['serial_number'].native
    cert = cerca_certificato_per_serial(cert_list, serial)
    if cert:
        subject = cert.subject
        validity = cert['tbs_certificate']['validity']
        not_before = validity['not_before'].native
        not_after = validity['not_after'].native
        
        info[_('Identity')] = estrai_nome_cognome(subject)
        info[_('Tax Code')] = estrai_codice_fiscale(subject)
        info[_('Organization')] = estrai_organization(subject)
        info[_('Valid from')] = not_before.strftime('%d/%m/%Y %H:%M:%S') if isinstance(not_before, datetime) else str(not_before)
        info[_('Valid until')] = not_after.strftime('%d/%m/%Y %H:%M:%S') if isinstance(not_after, datetime) else str(not_after)
        info[_('Certificate issued by')] = cert.issuer.human_friendly
        
        # Check if the certificate is expired
        now = datetime.now(not_after.tzinfo) if hasattr(not_after, 'tzinfo') and not_after.tzinfo else datetime.now()
        if now > not_after:
            info[_('Certificate status')] = f'⚠️ {_("Expired")}'
        elif now < not_before:
            info[_('Certificate status')] = f'⚠️ {_("Not yet valid")}'
        else:
            info[_('Certificate status')] = f'✓ {_("Valid")}'
    else:
        info[_('Error')] = _('Certificate not found for this signature.')
    
    # Extract signature date and time (signing time)
    if 'signed_attrs' in signer and signer['signed_attrs'] is not None:
        for attr in signer['signed_attrs']:
            if attr['type'].native == 'signing_time':
                signing_time = attr['values'].native[0]
                info[_('Signature date and time')] = signing_time.strftime('%d/%m/%Y %H:%M:%S') if isinstance(signing_time, datetime) else str(signing_time)
                
                # Check if the signature was valid at the time of signing
                if cert and isinstance(signing_time, datetime) and isinstance(not_before, datetime) and isinstance(not_after, datetime):
                    if not_before <= signing_time <= not_after:
                        info[_('Signature valid at signing time')] = f'✓ {_("Yes")}'
                    else:
                        info[_('Signature valid at signing time')] = f'✗ {_("No")} ({_("certificate not valid at signature date")})'
    
    return info

def analizza_busta(data, livello=1):
    """
    Analyze a P7M envelope (including nested) and extract signature information.
    Automatically supports Base64, DER and PEM format.
    """
    risultati = []
    
    # Detect and convert format if necessary
    if livello == 1:  # Only at first level
        formato, data_convertita = rileva_formato_p7m(data)
        data = data_convertita
    
    try:
        content_info = cms.ContentInfo.load(data)
        if content_info['content_type'].native == 'signed_data':
            signed_data = content_info['content']
            cert_list = estrai_certificati(signed_data)
            signer_infos = signed_data['signer_infos']
            for idx, signer in enumerate(signer_infos, 1):
                info_firma = mostra_info_firma(signer, cert_list)
                info_firma['firmatario_idx'] = idx
                info_firma['livello_busta'] = livello
                risultati.append(info_firma)
            # Look for nested data (content)
            encap_content = signed_data['encap_content_info']['content']
            if encap_content is not None:
                try:
                    risultati += analizza_busta(encap_content.native, livello + 1)
                except Exception:
                    pass
    except Exception:
        pass
    return risultati

def stampa_risultati(risultati):
    for info in risultati:
        print(f"\n--- Firmatario {info.get('firmatario_idx', '?')} (Livello busta {info.get('livello_busta', '?')}) ---")
        for chiave, valore in info.items():
            if chiave not in ('firmatario_idx', 'livello_busta'):
                print(f"{chiave}: {valore}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(_('Usage: python signature_parser.py file.p7m'))
        sys.exit(1)
    else:
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
        risultati = analizza_busta(data)
        stampa_risultati(risultati)
