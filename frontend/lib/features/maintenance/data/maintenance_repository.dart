import 'package:dio/dio.dart';

import '../../../core/api_client.dart';
import '../../../core/offline/offline_cache.dart';

List<Map<String, dynamic>> _decodeList(Object raw) =>
    List<Map<String, dynamic>>.from(
      (raw as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );

class MaintenanceRepository {
  MaintenanceRepository(this._client);
  final ApiClient _client;

  Future<CachedResult<List<Map<String, dynamic>>>> failuresCached({
    String? block,
  }) {
    final key = block == null ? 'maint:failures:_all' : 'maint:failures:$block';
    return OfflineCache.instance.cached<List<Map<String, dynamic>>>(
      key: key,
      fetch: () async {
        final r = await _client.dio.get(
          '/v1/maintenance/failures',
          queryParameters: {'block': ?block},
        );
        return _decodeList(r.data as Object);
      },
      decode: _decodeList,
      encode: (items) => items,
    );
  }

  Future<CachedResult<List<Map<String, dynamic>>>> interventionsCached() {
    return OfflineCache.instance.cached<List<Map<String, dynamic>>>(
      key: 'maint:interventions',
      fetch: () async {
        final r = await _client.dio.get('/v1/maintenance/interventions');
        return _decodeList(r.data as Object);
      },
      decode: _decodeList,
      encode: (items) => items,
    );
  }

  Future<Map<String, dynamic>> reportFailure({
    required String date,
    required String block,
    String? wellCode,
    required String type,
    required String severity,
    String? description,
    int? estimatedDurationH,
  }) async {
    final r = await _client.dio.post('/v1/maintenance/failures', data: {
      'notification_date': date,
      'block': block,
      'well_code': ?wellCode,
      'failure_type': type,
      'severity': severity,
      'description': ?description,
      'estimated_duration_h': ?estimatedDurationH,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> updateFailure({
    required String failureId,
    String? status,
    String? severity,
    String? assignedTo,
    String? description,
    double? repairCost,
  }) async {
    final r = await _client.dio.patch('/v1/maintenance/failures/$failureId', data: {
      'status': ?status,
      'severity': ?severity,
      'assigned_to': ?assignedTo,
      'description': ?description,
      'repair_cost': ?repairCost,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> createIntervention({
    required String date,
    required String type,
    String? failureId,
    double? durationH,
    String? result,
    double? cost,
    String? notes,
  }) async {
    final r = await _client.dio.post('/v1/maintenance/interventions', data: {
      'failure_id': ?failureId,
      'intervention_date': date,
      'intervention_type': type,
      'duration_h': ?durationH,
      'result': ?result,
      'cost': ?cost,
      'notes': ?notes,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> updateIntervention({
    required String interventionId,
    double? durationH,
    String? result,
    double? cost,
    String? notes,
  }) async {
    final r = await _client.dio.patch(
      '/v1/maintenance/interventions/$interventionId',
      data: {
        'duration_h': ?durationH,
        'result': ?result,
        'cost': ?cost,
        'notes': ?notes,
      },
    );
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> uploadFailureAttachment({
    required String failureId,
    required String filename,
    required List<int> bytes,
    required String mimeType,
  }) async {
    final form = FormData.fromMap({
      'upload': MultipartFile.fromBytes(
        bytes,
        filename: filename,
        contentType: DioMediaType.parse(mimeType),
      ),
    });
    final r = await _client.dio.post(
      '/v1/maintenance/failures/$failureId/attachments',
      data: form,
    );
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<List<Map<String, dynamic>>> listFailureAttachments(String failureId) async {
    final r = await _client.dio.get(
      '/v1/maintenance/failures/$failureId/attachments',
    );
    return List<Map<String, dynamic>>.from(
      (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );
  }

  Future<Map<String, dynamic>> predictRisk({
    required String block,
    int horizonDays = 7,
  }) async {
    final r = await _client.dio.post(
      '/v1/ml/predict/maintenance',
      data: {'block': block, 'horizon_days': horizonDays},
    );
    return Map<String, dynamic>.from(r.data as Map);
  }
}
