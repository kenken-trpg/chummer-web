import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarFlags({ d }: SidebarBlockProps) {
  return (
    <>
      {d.ambidextrous ? (
        <div className="stat">
          <span>利き手</span>
          <b>両利き</b>
        </div>
      ) : null}
      {d.erased ? (
        <div className="stat">
          <span>身元</span>
          <b>Erased（周知度上限1）</b>
        </div>
      ) : null}
      {d.excon ? (
        <div className="stat">
          <span>経歴</span>
          <b>Ex-Con</b>
        </div>
      ) : null}
      {d.overclocker ? (
        <div className="stat">
          <span>オーバークロック</span>
          <b>デッキ +1</b>
        </div>
      ) : null}
      {(d.special_modification_limit?.max || 0) > 0 ? (
        <div className="stat">
          <span>特別改造</span>
          <b>
            {d.special_modification_limit?.used || 0} / {d.special_modification_limit?.max}
          </b>
        </div>
      ) : null}
      {d.friends_in_high_places ? (
        <div className="stat">
          <span>コンタクト</span>
          <b>FiHP</b>
        </div>
      ) : null}
      {d.made_man ? (
        <div className="stat">
          <span>組織</span>
          <b>Made Man</b>
        </div>
      ) : null}
      {(d.trustfund || 0) > 0 ? (
        <div className="stat">
          <span>信託</span>
          <b>
            TF{d.trustfund}
            {d.trustfund_label ? `（${d.trustfund_label}）` : ""}
          </b>
        </div>
      ) : null}
      {(d.dealer_connection_categories || []).length ? (
        <div className="stat">
          <span>ディーラー</span>
          <b>{(d.dealer_connection_categories || []).join(", ")} −10%</b>
        </div>
      ) : null}
    </>
  );
}
