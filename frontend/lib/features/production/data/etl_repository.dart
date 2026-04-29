import 'package:dio/dio.dart';

import '../../../core/api_client.dart';

/// Wrapper autour des endpoints /v1/etl/* (inspect + selective + legacy).
class EtlRepository {
  EtlRepository(this._client);
  final ApiClient _client;

  /// Step 1 — Analyse un fichier Excel sans rien insérer.
  /// Retourne `{snapshot_id, sheets: [...]}`.
  Future<Map<String, dynamic>> inspectExcel({
    required String filename,
    required List<int> bytes,
    String? label,
  }) async {
    final form = FormData.fromMap({
      'upload': MultipartFile.fromBytes(bytes, filename: filename),
    });
    final r = await _client.dio.post(
      '/v1/etl/inspect/excel',
      data: form,
      queryParameters: {
        if (label != null && label.isNotEmpty) 'label': label,
      },
    );
    return Map<String, dynamic>.from(r.data as Map);
  }

  /// Step 2 — Ingère uniquement les onglets sélectionnés depuis un snapshot
  /// précédemment uploadé via [inspectExcel].
  Future<Map<String, dynamic>> ingestSelective({
    required String snapshotId,
    required List<String> sheets,
  }) async {
    final r = await _client.dio.post(
      '/v1/etl/ingest/excel/selective',
      data: {
        'snapshot_id': snapshotId,
        'sheets': sheets,
      },
    );
    return Map<String, dynamic>.from(r.data as Map);
  }

  /// Legacy single-shot endpoint — gardé pour compatibilité avec l'ancien
  /// dialog mais le wizard utilise désormais [inspectExcel] + [ingestSelective].
  Future<Map<String, dynamic>> ingestExcel({
    required String filename,
    required List<int> bytes,
    String? label,
  }) async {
    final form = FormData.fromMap({
      'upload': MultipartFile.fromBytes(bytes, filename: filename),
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
