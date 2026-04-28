import 'package:dio/dio.dart';

import '../../../core/api_client.dart';

/// Wrapper minimaliste autour de l'endpoint /v1/etl/ingest/excel.
class EtlRepository {
  EtlRepository(this._client);
  final ApiClient _client;

  /// Envoie un fichier Excel (web : bytes ; mobile/desktop : path).
  /// Retourne la réponse brute du backend (snapshot_id, run_id, status,
  /// rows_processed, rows_skipped, rows_failed).
  Future<Map<String, dynamic>> ingestExcel({
    required String filename,
    required List<int> bytes,
    String? label,
  }) async {
    final form = FormData.fromMap({
      'upload': MultipartFile.fromBytes(
        bytes,
        filename: filename,
      ),
    });
    final r = await _client.dio.post(
      '/v1/etl/ingest/excel',
      data: form,
      queryParameters: {
        if (label != null && label.isNotEmpty) 'label': label,
      },
    );
    return Map<String, dynamic>.from(r.data as Map);
  }
}
