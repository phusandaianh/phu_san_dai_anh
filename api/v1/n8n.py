# -*- coding: utf-8 -*-
"""API lệnh cho N8N — automation phòng khám."""
from flask import Blueprint, request, jsonify

n8n_bp = Blueprint('n8n', __name__)


@n8n_bp.route('/commands', methods=['GET'])
def n8n_list_commands():
  from n8n_commands import verify_n8n_request, COMMAND_CATALOG, get_n8n_api_key
  ok, err = verify_n8n_request()
  if not ok:
    status = 503 if 'cấu hình' in (err or '').lower() else 401
    return jsonify({'success': False, 'error': err}), status
  return jsonify({
    'success': True,
    'configured': bool(get_n8n_api_key()),
    'endpoint': 'POST /api/n8n/command',
    'commands': COMMAND_CATALOG,
  })


@n8n_bp.route('/command', methods=['POST'])
def n8n_run_command():
  from n8n_commands import verify_n8n_request, execute_n8n_command, N8nCommandError

  ok, err = verify_n8n_request()
  if not ok:
    status = 503 if err and 'cấu hình' in err.lower() else 401
    return jsonify({'success': False, 'error': err}), status

  body = request.get_json(silent=True) or {}
  try:
    result = execute_n8n_command(body)
    return jsonify(result)
  except N8nCommandError as e:
    payload = {'success': False, 'error': e.message, 'code': e.code}
    if e.details is not None:
      payload['details'] = e.details
    return jsonify(payload), e.status
  except Exception as e:
    return jsonify({'success': False, 'error': str(e), 'code': 'internal_error'}), 500
