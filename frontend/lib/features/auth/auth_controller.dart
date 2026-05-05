import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_error.dart';
import '../../core/providers.dart';
import 'data/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(apiClientProvider)),
);

class AuthState {
  const AuthState({
    this.user,
    this.loading = false,
    this.error,
    this.bootstrapped = false,
  });
  final Map<String, dynamic>? user;
  final bool loading;
  final String? error;
  final bool bootstrapped;

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    Map<String, dynamic>? user,
    bool? loading,
    String? error,
    bool? bootstrapped,
    bool clearUser = false,
    bool clearError = false,
  }) =>
      AuthState(
        user: clearUser ? null : (user ?? this.user),
        loading: loading ?? this.loading,
        error: clearError ? null : (error ?? this.error),
        bootstrapped: bootstrapped ?? this.bootstrapped,
      );
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._repo) : super(const AuthState(loading: true)) {
    _bootstrap();
  }
  final AuthRepository _repo;

  // Tente de restaurer la session au démarrage : appel /me qui, sans access
  // token en mémoire, déclenche le 401 → l'intercepteur lit le refresh_token
  // depuis FlutterSecureStorage et rejoue la requête avec un access frais.
  Future<void> _bootstrap() async {
    try {
      final me = await _repo.me();
      state = const AuthState(bootstrapped: true).copyWith(user: me);
    } catch (_) {
      state = const AuthState(bootstrapped: true);
    }
  }

  Future<void> login(String email, String password, {String? mfaCode}) async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      await _repo.login(email: email, password: password, mfaCode: mfaCode);
      final me = await _repo.me();
      state = state.copyWith(user: me, loading: false);
    } catch (e) {
      state = state.copyWith(loading: false, error: prettyError(e));
    }
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthState(bootstrapped: true);
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.watch(authRepositoryProvider));
});
