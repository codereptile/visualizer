#include <iostream>
#include <vector>
#include <climits>

#define NEUTRAL INT_MIN
#define LAZY_NEUTRAL 0
#define LAZY_FUNC(a, b) a + b
#define FUNC(a, b) std::max(a, b)

struct node {
    long long l, r;
    long long value = NEUTRAL;
    long long lazy = 0;
    node *L = nullptr, *R = nullptr;

    node(long long l_, long long r_) : l(l_), r(r_) {};

    long long get_value() {
        return value + lazy;
    }

    void push() {
        if (L != nullptr) {
            L->lazy = LAZY_FUNC(L->lazy, lazy);
            R->lazy = LAZY_FUNC(R->lazy, lazy);
            value = FUNC(L->get_value(), R->get_value());
        } else {
            value = LAZY_FUNC(value, lazy);
        }
        lazy = LAZY_NEUTRAL;
    }

    void update() {
        if (L != nullptr) {
            value = FUNC(L->get_value(), R->get_value());
        } else {
            value = LAZY_FUNC(value, lazy);
        }
    }
};

void build(node *root, std::vector<long long> &arr) {
    if (root->r - root->l == 1) {
        if (root->l < arr.size()) {
            root->value = arr[root->l];
        }
    } else {
        root->L = new node(root->l, root->l / 2 + root->r / 2);
        root->R = new node(root->l / 2 + root->r / 2, root->r);

        build(root->L, arr);
        build(root->R, arr);
        root->value = FUNC(root->L->value, root->R->value);
    }
}

void print(node *root, long long depth = 0) {
    if (root == nullptr) {
        return;
    }
    print(root->R, depth + 1);
    for (int i = 0; i < depth; ++i) {
        std::cout << "\t";
    }
    std::cout << root->value << "/" << root->lazy << "\n";
    print(root->L, depth + 1);
}

long long ans(node *root, long long lq, long long rq) {
    root->push();
    if (root->l >= rq || root->r <= lq) {
        return NEUTRAL;
    } else if (lq <= root->l && root->r <= rq) {
        return root->get_value();
    } else {
        return FUNC(ans(root->L, lq, rq), ans(root->R, lq, rq));
    }
}

void set_lazy(node *root, long long lq, long long rq, long long lazy) {
    root->push();
    if (root->l >= rq || root->r <= lq) {
        return;
    } else if (lq <= root->l && root->r <= rq) {
        root->lazy = lazy;
    } else {
        set_lazy(root->L, lq, rq, lazy);
        set_lazy(root->R, lq, rq, lazy);
        root->update();
    }
}

int main() {
    long long n;
    std::cin >> n;
    std::vector<long long> arr(n);
    for (long long i = 0; i < n; ++i) {
        std::cin >> arr[i];
    }

    long long p = 0;
    while (1 << p < n) p++;

    node *root = new node(0, 1 << p);
    build(root, arr);

    long long m;
    std::cin >> m;
    for (long long K = 0; K < m; K++) {
        char c;
        std::cin >> c;
        if (c == 'm') {
            long long l, r;
            std::cin >> l >> r;
            std::cout << ans(root, l - 1, r) << "\n";
        }
        if (c == 'a') {
            long long l, r, add;
            std::cin >> l >> r >> add;
            set_lazy(root, l - 1, r, add);
        }
    }
}