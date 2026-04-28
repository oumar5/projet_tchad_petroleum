import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/configuration/data/blocks_repository.dart';
import '../providers.dart';

final blocksRepositoryProvider = Provider<BlocksRepository>(
  (ref) => BlocksRepository(ref.watch(apiClientProvider)),
);

/// Cached list of all zones — invalidated by Configuration on create/update/delete.
final zonesProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(blocksRepositoryProvider).listZones(),
);

/// Cached list of blocks, optionally filtered by zone code.
/// Pass `null` to fetch every block.
final blocksProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String?>(
  (ref, zoneCode) =>
      ref.watch(blocksRepositoryProvider).listBlocks(zoneCode: zoneCode),
);

final wellsProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String?>(
  (ref, blockCode) =>
      ref.watch(blocksRepositoryProvider).listWells(blockCode: blockCode),
);

/// Currently selected zone code (null = "Toutes les zones").
final selectedZoneProvider = StateProvider<String?>((ref) => null);

/// Currently selected block code (shared across screens).
final selectedBlockProvider = StateProvider<String>((ref) => 'X');
