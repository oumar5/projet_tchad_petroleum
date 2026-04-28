import 'package:flutter/material.dart';

import '../api_error.dart';

class ErrorState extends StatelessWidget {
  const ErrorState({
    super.key,
    required this.error,
    this.onRetry,
    this.title,
  });

  final Object error;
  final VoidCallback? onRetry;
  final String? title;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 360),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: scheme.errorContainer.withValues(alpha: 0.6),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.error_outline_rounded,
                  size: 36,
                  color: scheme.error,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                title ?? 'Impossible de charger les données',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              Text(
                prettyError(error),
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
                textAlign: TextAlign.center,
              ),
              if (onRetry != null) ...[
                const SizedBox(height: 20),
                FilledButton.tonalIcon(
                  onPressed: onRetry,
                  icon: const Icon(Icons.refresh_rounded),
                  label: const Text('Réessayer'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
