import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/configuration/data/blocks_repository.dart';
import '../offline/cache_status.dart';
import '../offline/offline_cache.dart';
import '../providers.dart';

final blocksRepositoryProvider = Provider<BlocksRepository>(
  (ref) => BlocksRepository(ref.watch(apiClientProvider)),
);

const _kZonesKey = 'configuration.zones';
String _kBlocksKey(String? z) =>
    z == null ? 'configuration.blocks._all' : 'configuration.blocks.$z';
String _kWellsKey(String? b) =>
    b == null ? 'configuration.wells._all' : 'configuration.wells.$b';

/// Cached list of all zones — invalidated by Configuration on create/update/delete.
final zonesProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) async {
    final r = await ref.watch(blocksRepositoryProvider).listZonesCached();
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kZonesKey, CacheStatus.fromResult(r));
    return r.data;
  },
);

/// Cached list of blocks, optionally filtered by zone code.
/// Pass `null` to fetch every block.
final blocksProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String?>(
  (ref, zoneCode) async {
    final r = await ref
        .watch(blocksRepositoryProvider)
        .listBlocksCached(zoneCode: zoneCode);
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kBlocksKey(zoneCode), CacheStatus.fromResult(r));
    return r.data;
  },
);

final wellsProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String?>(
  (ref, blockCode) async {
    final r = await ref
        .watch(blocksRepositoryProvider)
        .listWellsCached(blockCode: blockCode);
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kWellsKey(blockCode), CacheStatus.fromResult(r));
    return r.data;
  },
);

const _kSelectedZoneKey = 'prefs:selected_zone';
const _kSelectedBlockKey = 'prefs:selected_block';

/// Currently selected zone code (null = "Toutes les zones"). Persisted to Hive.
final selectedZoneProvider = StateProvider<String?>((ref) {
  return OfflineCache.instance.getString(_kSelectedZoneKey);
});

/// Currently selected block code (shared across screens). Persisted to Hive.
final selectedBlockProvider = StateProvider<String>((ref) {
  return OfflineCache.instance.getString(_kSelectedBlockKey) ?? 'X';
});

/// Call once at app startup to wire selection persistence.
void registerSelectionPersistence(WidgetRef ref) {
  ref.listen<String?>(selectedZoneProvider, (_, next) {
    if (next == null) {
      OfflineCache.instance.deleteString(_kSelectedZoneKey);
    } else {
      OfflineCache.instance.putString(_kSelectedZoneKey, next);
    }
  });
  ref.listen<String>(selectedBlockProvider, (_, next) {
    OfflineCache.instance.putString(_kSelectedBlockKey, next);
  });
}
