import '../../../core/api_client.dart';

class MaintenanceRepository {
  MaintenanceRepository(this._client);
  final ApiClient _client;

  Future<List<Map<String, dynamic>>> failures({String? block}) async {
    final r = await _client.dio.get(
      '/v1/maintenance/failures',
      queryParameters: {'block': ?block},
    );
    return List<Map<String, dynamic>>.from(
      (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );
  }

  Future<List<Map<String, dynamic>>> interventions() async {
    final r = await _client.dio.get('/v1/maintenance/interventions');
    return List<Map<String, dynamic>>.from(
      (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );
  }

  Future<void> reportFailure({
    required String date,
    required String block,
    required String type,
    required String severity,
    String? description,
  }) async {
    await _client.dio.post('/v1/maintenance/failures', data: {
      'notification_date': date,
      'block': block,
      'failure_type': type,
      'severity': severity,
      'description': ?description,
    });
  }
}
