import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/configuration/data/blocks_repository.dart';
import '../providers.dart';

final blocksRepositoryProvider = Provider<BlocksRepository>(
  (ref) => BlocksRepository(ref.watch(apiClientProvider)),
);

/// Cached list of all blocks — invalidated by the configuration page on
/// create/update/delete.
final blocksProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(blocksRepositoryProvider).listBlocks(),
);

final wellsProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String?>(
  (ref, blockCode) =>
      ref.watch(blocksRepositoryProvider).listWells(blockCode: blockCode),
);

/// Currently selected block code (shared across screens).
final selectedBlockProvider = StateProvider<String>((ref) => 'X');
