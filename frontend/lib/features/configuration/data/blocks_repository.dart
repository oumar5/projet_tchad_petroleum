import '../../../core/api_client.dart';

class BlocksRepository {
  BlocksRepository(this._client);
  final ApiClient _client;

  // ----- Zones -----

  Future<List<Map<String, dynamic>>> listZones() async {
    final r = await _client.dio.get('/v1/production/zones');
    return List<Map<String, dynamic>>.from(
      (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );
  }

  Future<Map<String, dynamic>> createZone({
    required String code,
    required String name,
    String? description,
  }) async {
    final r = await _client.dio.post('/v1/production/zones', data: {
      'code': code,
      'name': name,
      'description': ?description,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> updateZone({
    required String zoneId,
    String? name,
    String? description,
  }) async {
    final r = await _client.dio.patch('/v1/production/zones/$zoneId', data: {
      'name': ?name,
      'description': ?description,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<void> deleteZone(String zoneId) async {
    await _client.dio.delete('/v1/production/zones/$zoneId');
  }

  // ----- Blocks -----

  Future<List<Map<String, dynamic>>> listBlocks({String? zoneCode}) async {
    final r = await _client.dio.get(
      '/v1/production/blocks',
      queryParameters: {'zone': ?zoneCode},
    );
    return List<Map<String, dynamic>>.from(
      (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );
  }

  Future<Map<String, dynamic>> createBlock({
    required String code,
    required String name,
    required String zoneId,
    String? description,
  }) async {
    final r = await _client.dio.post('/v1/production/blocks', data: {
      'code': code,
      'name': name,
      'zone_id': zoneId,
      'description': ?description,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> updateBlock({
    required String blockId,
    String? name,
    String? description,
    String? zoneId,
  }) async {
    final r = await _client.dio.patch('/v1/production/blocks/$blockId', data: {
      'name': ?name,
      'description': ?description,
      'zone_id': ?zoneId,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<void> deleteBlock(String blockId) async {
    await _client.dio.delete('/v1/production/blocks/$blockId');
  }

  Future<List<Map<String, dynamic>>> listWells({String? blockCode}) async {
    final r = await _client.dio.get(
      '/v1/production/wells',
      queryParameters: {'block': ?blockCode},
    );
    return List<Map<String, dynamic>>.from(
      (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );
  }

  Future<Map<String, dynamic>> createWell({
    required String code,
    required String blockId,
    String? pumpType,
    bool isActive = true,
  }) async {
    final r = await _client.dio.post('/v1/production/wells', data: {
      'code': code,
      'block_id': blockId,
      'pump_type': ?pumpType,
      'is_active': isActive,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<Map<String, dynamic>> updateWell({
    required String wellId,
    String? blockId,
    String? pumpType,
    bool? isActive,
  }) async {
    final r = await _client.dio.patch('/v1/production/wells/$wellId', data: {
      'block_id': ?blockId,
      'pump_type': ?pumpType,
      'is_active': ?isActive,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<void> deleteWell(String wellId) async {
    await _client.dio.delete('/v1/production/wells/$wellId');
  }
}
