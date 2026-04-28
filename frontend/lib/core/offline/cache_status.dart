import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'offline_cache.dart';

/// Per-feature cache status. Each repository writes here when it falls back
/// to a cached payload, so any UI can subscribe and show the offline banner.
class CacheStatus {
  const CacheStatus({
    required this.fromCache,
    this.fetchedAt,
    this.stale = false,
  });

  const CacheStatus.live() : this(fromCache: false);

  final bool fromCache;
  final DateTime? fetchedAt;
  final bool stale;

  CacheStatus.fromResult(CachedResult<dynamic> r)
      : fromCache = r.fromCache,
        fetchedAt = r.fromCache ? r.fetchedAt : null,
        stale = r.staleSinceFresh ?? false;
}

/// Map of `feature_key → CacheStatus`. Repositories notify here so widgets
/// can pick up offline state without prop drilling.
class CacheStatusNotifier extends StateNotifier<Map<String, CacheStatus>> {
  CacheStatusNotifier() : super(const {});

  void report(String key, CacheStatus status) {
    state = {...state, key: status};
  }

  void clear(String key) {
    if (!state.containsKey(key)) return;
    final next = Map<String, CacheStatus>.from(state)..remove(key);
    state = next;
  }
}

final cacheStatusProvider =
    StateNotifierProvider<CacheStatusNotifier, Map<String, CacheStatus>>(
  (ref) => CacheStatusNotifier(),
);

/// Banner shown in screens whose data is currently served from cache.
///
/// Two modes:
/// * [featureKey] given → watch only that feature's status.
/// * [featureKey] null → aggregate any feature currently in cache mode
///   (banner appears as long as *anything* is offline).
class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key, this.featureKey});
  final String? featureKey;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final all = ref.watch(cacheStatusProvider);
    CacheStatus? status;
    if (featureKey != null) {
      status = all[featureKey!];
    } else {
      final cached = all.values.where((s) => s.fromCache).toList();
      if (cached.isEmpty) {
        status = null;
      } else {
        // Pick oldest fetched as representative.
        cached.sort((a, b) =>
            (a.fetchedAt ?? DateTime.now())
                .compareTo(b.fetchedAt ?? DateTime.now()));
        status = cached.first;
      }
    }
    if (status == null || !status.fromCache) return const SizedBox.shrink();

    final scheme = Theme.of(context).colorScheme;
    final ts = status.fetchedAt;
    final ageLabel = ts == null ? '' : _formatAge(DateTime.now().difference(ts));
    final bg = status.stale
        ? scheme.errorContainer.withValues(alpha: 0.6)
        : scheme.tertiaryContainer.withValues(alpha: 0.5);
    final fg = status.stale ? scheme.onErrorContainer : scheme.onTertiaryContainer;

    return Material(
      color: bg,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          children: [
            Icon(Icons.cloud_off_rounded, size: 18, color: fg),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                status.stale
                    ? 'Hors ligne · données potentiellement obsolètes ($ageLabel)'
                    : 'Hors ligne · dernières données mises en cache $ageLabel',
                style: TextStyle(color: fg, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
      ),
    );
  }

  static String _formatAge(Duration d) {
    if (d.inMinutes < 1) return 'à l\'instant';
    if (d.inHours < 1) return 'il y a ${d.inMinutes} min';
    if (d.inDays < 1) return 'il y a ${d.inHours} h';
    return 'il y a ${d.inDays} j';
  }
}
