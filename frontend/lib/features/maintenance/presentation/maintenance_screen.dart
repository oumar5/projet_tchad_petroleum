import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
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
          bottom: const TabBar(tabs: [
            Tab(text: 'Pannes'),
            Tab(text: 'Interventions'),
          ]),
        ),
        body: TabBarView(children: [
          _FailuresTab(),
          _InterventionsTab(),
        ]),
      ),
    );
  }
}

class _FailuresTab extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final failures = ref.watch(_failuresProvider);
    return failures.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Erreur : $e')),
      data: (items) => ListView.separated(
        itemCount: items.length,
        separatorBuilder: (_, _) => const Divider(height: 1),
        itemBuilder: (_, i) {
          final f = items[i];
          return ListTile(
            leading: _severityIcon(f['severity'] as String),
            title: Text('${f['block']} — ${f['failure_type']}'),
            subtitle: Text('${f['notification_date']} · ${f['description'] ?? ''}'),
            trailing: f['resolved_at'] != null
                ? const Icon(Icons.check, color: Colors.green)
                : null,
          );
        },
      ),
    );
  }

  Widget _severityIcon(String sev) {
    final map = {
      'low': Colors.blue,
      'medium': Colors.orange,
      'high': Colors.red,
      'critical': Colors.purple,
    };
    return CircleAvatar(backgroundColor: map[sev] ?? Colors.grey, radius: 8);
  }
}

class _InterventionsTab extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(_interventionsProvider);
    return items.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Erreur : $e')),
      data: (rows) => ListView.separated(
        itemCount: rows.length,
        separatorBuilder: (_, _) => const Divider(height: 1),
        itemBuilder: (_, i) {
          final r = rows[i];
          return ListTile(
            title: Text('${r['intervention_date']} — ${r['intervention_type']}'),
            subtitle: Text(r['result']?.toString() ?? '—'),
            trailing: Text('${r['duration_h'] ?? '—'} h'),
          );
        },
      ),
    );
  }
}
