import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/offline/cache_status.dart';
import '../../../core/providers.dart';
import '../../../core/providers/blocks_providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/kpi_card.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/zone_block_picker.dart';
import '../data/maintenance_repository.dart';

const _kFailuresKey = 'maintenance.failures';
const _kInterventionsKey = 'maintenance.interventions';

final _repoProvider = Provider<MaintenanceRepository>(
  (ref) => MaintenanceRepository(ref.watch(apiClientProvider)),
);

final _failuresProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) async {
    final r = await ref.watch(_repoProvider).failuresCached();
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kFailuresKey, CacheStatus.fromResult(r));
    return r.data;
  },
);

final _interventionsProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) async {
    final r = await ref.watch(_repoProvider).interventionsCached();
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kInterventionsKey, CacheStatus.fromResult(r));
    return r.data;
  },
);

class MaintenanceScreen extends ConsumerWidget {
  const MaintenanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Maintenance'),
          bottom: const TabBar(
            indicatorWeight: 3,
            labelStyle: TextStyle(fontWeight: FontWeight.w700),
            isScrollable: true,
            tabs: [
              Tab(icon: Icon(Icons.psychology_alt_rounded), text: 'Risque ML'),
              Tab(icon: Icon(Icons.warning_amber_rounded), text: 'Pannes'),
              Tab(icon: Icon(Icons.build_circle_rounded), text: 'Interventions'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [_RiskTab(), _FailuresTab(), _InterventionsTab()],
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

// ----------------------------------------------------------------------------
// Tab 1 — ML risk prediction
// ----------------------------------------------------------------------------

class _RiskTab extends ConsumerStatefulWidget {
  const _RiskTab();

  @override
  ConsumerState<_RiskTab> createState() => _RiskTabState();
}

class _RiskTabState extends ConsumerState<_RiskTab> {
  int _horizon = 7;
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _run());
  }

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final block = ref.read(selectedBlockProvider);
      final r = await ref.read(_repoProvider).predictRisk(
            block: block,
            horizonDays: _horizon,
          );
      setState(() => _result = r);
    } catch (e) {
      setState(() => _error = prettyError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Paramètres',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 16),
                const ZoneBlockPicker(),
                const SizedBox(height: 12),
                LayoutBuilder(
                  builder: (ctx, c) {
                    final stack = c.maxWidth < 480;
                    final left = DropdownButtonFormField<int>(
                      initialValue: _horizon,
                      decoration: const InputDecoration(
                        labelText: 'Horizon (jours)',
                        prefixIcon: Icon(Icons.event_repeat_rounded),
                      ),
                      items: [3, 7, 14, 30]
                          .map((d) => DropdownMenuItem(
                              value: d, child: Text('$d jours')))
                          .toList(),
                      onChanged: (v) => setState(() => _horizon = v ?? 7),
                    );
                    final right = const SizedBox.shrink();
                    if (stack) {
                      return Column(children: [
                        left,
                        const SizedBox(height: 12),
                        right,
                      ]);
                    }
                    return Row(children: [
                      Expanded(child: left),
                      const SizedBox(width: 12),
                      Expanded(child: right),
                    ]);
                  },
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _loading ? null : _run,
                  icon: _loading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.online_prediction_rounded),
                  label: Text(_loading
                      ? 'Calcul…'
                      : 'Évaluer le risque de panne'),
                ),
              ],
            ),
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          Card(
            color: scheme.errorContainer.withValues(alpha: 0.6),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: scheme.error),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _error!,
                      style: TextStyle(
                        color: scheme.onErrorContainer,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 20),
        if (_result == null && _error == null && !_loading)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 40),
            child: EmptyState(
              icon: Icons.psychology_alt_rounded,
              title: 'Aucune analyse ML disponible',
              subtitle:
                  'Sélectionne un bloc et un horizon pour obtenir le risque.',
            ),
          )
        else if (_result != null)
          _RiskResult(result: _result!),
      ],
    );
  }
}

class _RiskResult extends StatelessWidget {
  const _RiskResult({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final preds = result['predictions'];
    final first = preds is List && preds.isNotEmpty
        ? Map<String, dynamic>.from(preds.first as Map)
        : <String, dynamic>{};

    final maxRisk = (first['max_failure_risk'] as num?)?.toDouble() ?? 0;
    final avgRisk = (first['avg_failure_risk_30d'] as num?)?.toDouble() ?? 0;
    final level = (first['risk_level'] ?? 'low').toString();
    final block = (first['block'] ?? '—').toString();
    final horizon = (first['horizon_days'] ?? '').toString();
    final asOf = first['as_of']?.toString();
    final confidence = (result['confidence'] as num?)?.toDouble();

    final modelMap = result['model'];
    final modelName = modelMap is Map
        ? '${modelMap['name'] ?? '—'} ${modelMap['version'] ?? ''}'
        : '—';

    final entry = _severityMap[level] ?? ('Inconnu', AppColors.tealAccent);
    final color = entry.$2;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: 'Bloc $block · horizon $horizon jours',
          subtitle: 'Modèle : $modelName${asOf != null ? " · données au ${fmtDate(asOf)}" : ""}',
        ),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                _RiskGauge(value: maxRisk, color: color),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    'Niveau ${entry.$1.toLowerCase()}',
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.w800,
                      fontSize: 13,
                      letterSpacing: 0.4,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Risque max sur la fenêtre',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (ctx, c) {
            final w = c.maxWidth < 480 ? c.maxWidth : (c.maxWidth - 12) / 2;
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: w,
                  child: KpiCard(
                    label: 'Risque moyen 30j',
                    value: '${(avgRisk * 100).toStringAsFixed(1)} %',
                    icon: Icons.show_chart_rounded,
                    iconColor: color,
                  ),
                ),
                SizedBox(
                  width: w,
                  child: KpiCard(
                    label: 'Confiance modèle',
                    value: confidence == null
                        ? '—'
                        : '${(confidence * 100).toStringAsFixed(0)} %',
                    icon: Icons.verified_rounded,
                    iconColor: AppColors.goodGreen,
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(Icons.lightbulb_outline_rounded,
                    color: AppColors.goldAmber, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _recommendation(level),
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  String _recommendation(String level) {
    switch (level) {
      case 'high':
        return 'Risque élevé : programmer une inspection préventive sous 48 h '
            'et préparer les pièces de rechange critiques.';
      case 'medium':
        return 'Risque modéré : renforcer la surveillance et planifier '
            'une intervention dans les 7 jours.';
      default:
        return 'Risque faible : poursuivre la maintenance planifiée habituelle.';
    }
  }
}

class _RiskGauge extends StatelessWidget {
  const _RiskGauge({required this.value, required this.color});
  final double value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final pct = (value * 100).clamp(0, 100).toDouble();
    return Column(
      children: [
        SizedBox(
          width: 160,
          height: 160,
          child: Stack(
            alignment: Alignment.center,
            children: [
              SizedBox.expand(
                child: CircularProgressIndicator(
                  value: 1,
                  strokeWidth: 14,
                  valueColor: AlwaysStoppedAnimation(
                    Theme.of(context).colorScheme.surfaceContainerHighest,
                  ),
                ),
              ),
              SizedBox.expand(
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: value.clamp(0.0, 1.0)),
                  duration: const Duration(milliseconds: 700),
                  curve: Curves.easeOutCubic,
                  builder: (_, v, _) => CircularProgressIndicator(
                    value: v,
                    strokeWidth: 14,
                    valueColor: AlwaysStoppedAnimation(color),
                    strokeCap: StrokeCap.round,
                  ),
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${pct.toStringAsFixed(1)}%',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: color,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'risque',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                      letterSpacing: 1.2,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ----------------------------------------------------------------------------
// Tab 2 — Pannes (existing)
// ----------------------------------------------------------------------------

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
              subtitle:
                  'C’est plutôt bonne nouvelle ! Les pannes saisies par les techniciens '
                  'ou détectées par les capteurs apparaîtront ici dès leur déclaration.',
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

// ----------------------------------------------------------------------------
// Tab 3 — Interventions (existing)
// ----------------------------------------------------------------------------

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
              title: 'Aucune intervention enregistrée',
              subtitle:
                  'Dès qu’une équipe déclare une intervention sur le terrain '
                  '(remplacement de pompe, nettoyage, contrôle…), elle s’affichera ici '
                  'avec sa durée et son coût.',
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
                    backgroundColor:
                        AppColors.tealAccent.withValues(alpha: 0.15),
                    child: const Icon(Icons.build_rounded,
                        color: AppColors.tealAccent),
                  ),
                  title: Text(
                    (r['intervention_type'] ?? '—').toString(),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(fmtDate(r['intervention_date'])),
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
