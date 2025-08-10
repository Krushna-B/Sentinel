
import { Sat } from "@/lib/api";

const R_EARTH_KM = 6371;   

type SatDetails = {
  norad_id: number;
  name?: string | null;
  cospar_id?: string | null;
  object_type?: string | null;
  country_code?: string | null;
  launch_date?: string | null;
};

interface GlobeCardHUDProps{
    objects: Sat[]
    selectedId: number | null
    details?: SatDetails | null
    onClose: () => void;    
}


export default function GlobeCardHUD({selectedId,objects,details, onClose}:GlobeCardHUDProps) {
  if (selectedId == null) return null;
  const obj = objects.find(o => o.norad_id === selectedId);

  return (
    <div className="pointer-events-none fixed top-4 right-4 z-50">
      <div className="pointer-events-auto w-[88vw] max-w-[420px] min-w-[280px]
                      p-4 rounded-xl border border-white/10 bg-black/80 backdrop-blur
                      shadow-xl">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1.5">
            <div className="text-sm font-semibold leading-tight">
              {details?.name ?? "Unknown object"}
            </div>

            <div className="text-xs text-neutral-300">
              NORAD: <span className="font-medium">{selectedId}</span>
              {details?.cospar_id && (
                <> · COSPAR: <span className="font-medium">{details.cospar_id}</span></>
              )}
            </div>
             {details?.object_type && (
              <div className="text-xs text-neutral-400">
                Object Type: {details.object_type}
              </div>
            )}
            {details?.launch_date && (
              <div className="text-xs text-neutral-400">
                Launch: {new Date(details.launch_date).toISOString().slice(0,10)}
              </div>
            )}

            {obj && (
              <div className="text-xs mt-1">
                lat <span className="font-medium">{obj.lat.toFixed(2)}°</span>,{" "}
                lon <span className="font-medium">{obj.lon.toFixed(2)}°</span>,{" "}
                alt <span className="font-medium">{Math.round(obj.alt).toLocaleString()} km</span>
              </div>
            )}
          </div>

          <button
            className="shrink-0 text-[11px] px-2.5 py-1 rounded-md
                       bg-white/10 hover:bg-white/20 active:bg-white/25 transition"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}