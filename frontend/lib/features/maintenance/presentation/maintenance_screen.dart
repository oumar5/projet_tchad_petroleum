import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../data/maintenance_repository.dart';

final _repoProvider = Provider<MaintenanceRepository>(
  (ref) => MaintenanceRepository(ref.watch(apiClientProvider)),
);

final _failuresProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(_repoProvider).failures(),
);

final _interventionsProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(_repoProvider).interventions(),
);

class MaintenanceScreen extends ConsumerWidget {
  const MaintenanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Maintenance'),
          bottom: TabBar(
            indicatorWeight: 3,
            labelStyle: const TextStyle(fontWeight: FontWeight.w700),
            tabs: const [
              Tab(icon: Icon(Icons.warning_amber_rounded), text: 'Pannes'),
              Tab(icon: Icon(Icons.build_circle_rounded), text: 'Interventions'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [_FailuresTab(), _InterventionsTab()],
        ),
      ),
    );
  }
}

const _severityMap = {
  'low': ('Faible', AppColors.tealAccent),
  'medium': ('Moyenne', AppColors.warnOrange),
  'high': ('Élevée', AppColors.dangerRed),
  'critical': ('Critique', Color(0xFF8E44AD)),
};

class _FailuresTab extends ConsumerWidget {
  const _FailuresTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final failures = ref.watch(_failuresProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_failuresProvider),
      child: failures.when(
        loading: () => const _LoadingList(),
        error: (e, _) => ErrorState(
          error: e,
          onRetry: () => ref.invalidate(_failuresProvider),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const EmptyState(
              icon: Icons.health_and_safety_outlined,
              title: 'Aucune panne déclarée',
              subtitle: 'Les nouvelles pannes apparaîtront ici en temps réel.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, i) => _FailureCard(row: items[i]),
          );
        },
      ),
    );
  }
}

class _FailureCard extends StatelessWidget {
  const _FailureCard({required this.row});
  final Map<String, dynamic> row;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final sev = (row['severity'] ?? 'low').toString();
    final entry = _severityMap[sev] ?? ('Inconnu', scheme.outline);
    final resolved = row['resolved_at'] != null;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 64,
              decoration: BoxDecoration(
                color: entry.$2,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        '${row['block'] ?? '—'} · ${row['failure_type'] ?? '—'}',
                        style: Theme.of(context).textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: entry.$2.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          entry.$1,
                          style: TextStyle(
                            color: entry.$2,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    fmtDate(row['notification_date']),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                  if (row['description'] != null) ...[
                    const SizedBox(height: 6),
                    Text(
                      row['description'].toString(),
                      style: Theme.of(context).textTheme.bodyMedium,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            if (resolved)
              const Icon(Icons.check_circle_rounded,
                  color: AppColors.goodGreen, size: 26)
            else
              Icon(Icons.pending_rounded,
                  color: scheme.onSurfaceVariant, size: 22),
          ],
        ),
      ),
    );
  }
}

class _InterventionsTab extends ConsumerWidget {
  const _InterventionsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(_interventionsProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_interventionsProvider),
      child: items.when(
        loading: () => const _LoadingList(),
        error: (e, _) => ErrorState(
          error: e,
          onRetry: () => ref.invalidate(_interventionsProvider),
        ),
        data: (rows) {
          if (rows.isEmpty) {
            return const EmptyState(
              icon: Icons.build_outlined,
              title: 'Aucune intervention',
              subtitle: 'Les interventions terminées s\'afficheront ici.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: rows.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final r = rows[i];
              return Card(
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 6),
                  leading: CircleAvatar(
                    backgroundColor: AppColors.tealAccent.withValues(
                      alpha: 0.15,
                    ),
                    child: const Icon(Icons.build_rounded,
                        color: AppColors.tealAccent),
                  ),
                  title: Text(
                    (r['intervention_type'] ?? '—').toString(),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(
                    fmtDate(r['intervention_date']),
                  ),
                  trailing: Text(
                    '${r['duration_h'] ?? '—'} h',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _LoadingList extends StatelessWidget {
  const _LoadingList();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 6,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (_, _) => const Skeleton(height: 80, radius: 12),
    );
  }
}
