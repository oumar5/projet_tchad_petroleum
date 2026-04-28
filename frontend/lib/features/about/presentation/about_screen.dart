import 'package:flutter/material.dart';

import '../../../core/theme.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  static const _appVersion = '3.0.0';

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('À propos')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // Hero
          Center(
            child: Column(
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [
                        AppColors.petrolDeep,
                        AppColors.tealAccent,
                      ],
                    ),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.petrolDeep.withValues(alpha: 0.3),
                        blurRadius: 24,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.local_gas_station_rounded,
                    color: Colors.white,
                    size: 40,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'SmartBarrel',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                  ),
                ),
                Text(
                  'Plateforme de production pétrolière — Tchad',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: scheme.primary.withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    'Version $_appVersion',
                    style: TextStyle(
                      color: scheme.primary,
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          _Section(
            title: 'Mission',
            child: Text(
              'Aider les opérateurs et les ingénieurs à anticiper les pannes, '
              'optimiser l\'injection d\'eau et prévoir la production grâce à '
              'l\'analyse de l\'historique réel des puits.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(height: 24),
          _Section(
            title: 'Pour qui ?',
            child: const Column(
              children: [
                _Persona(
                  icon: Icons.engineering_rounded,
                  label: 'Ingénieurs production',
                  text:
                      'Suivi quotidien, prévisions, recommandations d\'injection.',
                ),
                _Persona(
                  icon: Icons.health_and_safety_rounded,
                  label: 'Inspecteurs maintenance',
                  text: 'Risque de panne, planification des interventions.',
                ),
                _Persona(
                  icon: Icons.analytics_rounded,
                  label: 'Analystes & direction',
                  text: 'KPIs, tendances, exports CSV.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _Section(
            title: 'Architecture technique',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: const [
                _TechBadge('Flutter 3.x'),
                _TechBadge('FastAPI'),
                _TechBadge('PostgreSQL 16'),
                _TechBadge('Redis'),
                _TechBadge('RabbitMQ'),
                _TechBadge('Celery'),
                _TechBadge('scikit-learn'),
                _TechBadge('XGBoost'),
                _TechBadge('Docker Compose'),
                _TechBadge('Traefik'),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _Section(
            title: 'Sécurité',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _BulletPoint(
                  icon: Icons.lock_rounded,
                  text: 'Authentification JWT RS256 (15 min) + refresh 7 jours.',
                ),
                _BulletPoint(
                  icon: Icons.shield_rounded,
                  text: 'RBAC à 4 rôles : admin, ingénieur, analyste, lecteur.',
                ),
                _BulletPoint(
                  icon: Icons.verified_user_rounded,
                  text:
                      'Mots de passe hashés (bcrypt) + MFA TOTP optionnel.',
                ),
                _BulletPoint(
                  icon: Icons.history_rounded,
                  text: 'Audit log immuable de tous les événements sensibles.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _Section(
            title: 'Crédits',
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _BulletPoint(
                  icon: Icons.code_rounded,
                  text: 'Développement : équipe SmartBarrel.',
                ),
                _BulletPoint(
                  icon: Icons.school_rounded,
                  text: 'Recherche & ML : pipeline ported from the v2 study.',
                ),
                _BulletPoint(
                  icon: Icons.factory_rounded,
                  text:
                      'Données : historique de production des blocs X/Y/Z, Tchad.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          Center(
            child: Text(
              '© SmartBarrel 2026',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w800,
                letterSpacing: -0.2,
              ),
            ),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _Persona extends StatelessWidget {
  const _Persona({
    required this.icon,
    required this.label,
    required this.text,
  });
  final IconData icon;
  final String label;
  final String text;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: scheme.primary.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: scheme.primary, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  text,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BulletPoint extends StatelessWidget {
  const _BulletPoint({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: scheme.primary),
          const SizedBox(width: 10),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

class _TechBadge extends StatelessWidget {
  const _TechBadge(this.label);
  final String label;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          fontFamily: 'monospace',
        ),
      ),
    );
  }
}
