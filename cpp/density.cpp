#include "density.hpp"
#include "riemann.hpp"
#ifdef ADIFF
    #include "externals/ampi_interface_realreverse.cpp"
#endif

//// confirm that make_tuple doesn't create copies
void RCF::primitive(const scalar rho, const scalar rhoU[3], const scalar rhoE, scalar U[3], scalar& T, scalar& p) {
    scalar U2 = 0.;
    for (integer i = 0; i < 3; i++) {
        U[i] = rhoU[i]/rho;
        U2 += U[i]*U[i];
    }
    scalar e = rhoE/rho - 0.5*U2;
    T = e/this->Cv, 
    p = (this->gamma-1)*rho*e;
}

void RCF::conservative(const scalar U[3], const scalar T, const scalar p, scalar& rho, scalar rhoU[3], scalar& rhoE) {
    scalar e = this->Cv * T;
    rho = p/(e*(this->gamma - 1));
    scalar U2 = 0.;
    for (integer i = 0; i < 3; i++) {
        U2 += U[i]*U[i];
        rhoU[i] = rho*U[i];
    }
    rhoE = rho*(e + 0.5*U2);
}

//inline Ref<arr> internalField(arr& phi) {
    //Ref<arr> phiI = SELECT(phi, 0, mesh.nInternalCells);
    //return phiI;
//}

//inline Ref<arr> boundaryField(arr& phi) { 
    //Ref<arr> phiB = SELECT(phi, mesh.nInternalCells, mesh.nGhostCells);
    //return phiB;
//}

//inline arr mu(const arr& T) {
    //return 0*T;//1.4792e-06*T.pow(1.5)/(T+116);
//}
//inline arr kappa(const arr& mu, const arr& T) {
    //return mu*this->Cp/this->Pr;
//}
void RCF::getFlux(const scalar U[3], const scalar T, const scalar p, const uscalar N[3], scalar& rhoFlux, scalar rhoUFlux[3], scalar& rhoEFlux) {
    scalar rho, rhoU[3], rhoE;
    this->conservative(U, T, p, rho, rhoU, rhoE);
    scalar Un = 0.;
    for (integer i = 0; i < 3; i++) {
        Un += U[i]*N[i];
    }
    rhoFlux = rho*Un;
    for (integer i = 0; i < 3; i++) {
        rhoUFlux[i] = rhoU[i]*Un + p*N[i];
    }
    rhoEFlux = (rhoE + p)*Un;
}

void RCF::equation(const arr& rho, const arr& rhoU, const arr& rhoE, arr& drho, arr& drhoU, arr& drhoE) {
    // make decision between 1 and 3 a template
    // optimal memory layout? combine everything?
    //cout << "c++: equation 1" << endl;
    const Mesh& mesh = *this->mesh;

    arr U(mesh.nCells, 3);
    arr T(mesh.nCells);
    arr p(T.shape);
    for (integer i = 0; i < mesh.nInternalCells; i++) {
        this->primitive(rho(i), &rhoU(i), rhoE(i), &U(i), T(i), p(i));
    }
    //cout << "c++: equation 2" << endl;

    this->boundary(this->boundaries[0], U);
    this->boundary(this->boundaries[1], T);
    this->boundary(this->boundaries[2], p);

    arr gradU(mesh.nCells, 3, 3);
    arr gradT(mesh.nCells, 1, 3);
    arr gradp(gradT.shape);
    gradU.zero();
    gradT.zero();
    gradp.zero();
    auto faceUpdate = [&](integer start, integer end, bool neighbour) {
        for (integer i = start; i < end; i++) {
            scalar UF[3], TF, pF;
            this->interpolate->central(U, UF, i);
            this->interpolate->central(T, &TF, i);
            this->interpolate->central(p, &pF, i);
            this->operate->grad(UF, gradU, i, neighbour);
            this->operate->grad(&TF, gradT, i, neighbour);
            this->operate->grad(&pF, gradp, i, neighbour);
        }
    };
    faceUpdate(0, mesh.nInternalFaces, true);
    for (auto& patch: mesh.boundary) {
        auto& patchInfo = patch.second;
        integer startFace, nFaces;
        tie(startFace, nFaces) = mesh.boundaryFaces.at(patch.first);
        integer cellStartFace = mesh.nInternalCells + startFace - mesh.nInternalFaces;
        if (patchInfo.at("type") == "cyclic") {
            faceUpdate(startFace, startFace + nFaces, false);
        } else {
            for (integer i = 0; i < nFaces; i++) {
                integer index = startFace + i;
                integer c = cellStartFace + i;
                this->operate->grad(&U(c), gradU, index, false);
                this->operate->grad(&T(c), gradT, index, false);
                this->operate->grad(&p(c), gradp, index, false);
            }
        }
    }
    faceUpdate(mesh.nLocalFaces, mesh.nFaces, false);
    //cout << "gradU " << gradU.checkNAN() << endl;
    
    //cout << "c++: equation 3" << endl;
    this->boundary(mesh.defaultBoundary, gradU);
    this->boundary(mesh.defaultBoundary, gradT);
    this->boundary(mesh.defaultBoundary, gradp);
    
    drho.zero();
    drhoU.zero();
    drhoE.zero();
    auto faceFluxUpdate = [&](integer start, integer end, bool neighbour) {
        for (integer i = start; i < end; i++) {
            scalar ULF[3], URF[3];
            scalar TLF, TRF;
            scalar pLF, pRF;
            
            this->interpolate->secondOrder(U, gradU, ULF, i, 0);
            this->interpolate->secondOrder(U, gradU, URF, i, 1);
            this->interpolate->secondOrder(T, gradT, &TLF, i, 0);
            this->interpolate->secondOrder(T, gradT, &TRF, i, 1);
            this->interpolate->secondOrder(p, gradp, &pLF, i, 0);
            this->interpolate->secondOrder(p, gradp, &pRF, i, 1);

            scalar rhoLF, rhoRF;
            scalar rhoULF[3], rhoURF[3];
            scalar rhoELF, rhoERF;
            this->conservative(ULF, TLF, pLF, rhoLF, rhoULF, rhoELF);
            this->conservative(URF, TRF, pRF, rhoRF, rhoURF, rhoERF);
            scalar rhoFlux;
            scalar rhoUFlux[3];
            scalar rhoEFlux;
            riemannSolver(this->gamma, \
                pLF, pRF, TLF, TRF, ULF, URF, \
                rhoLF, rhoRF, rhoULF, rhoURF, rhoELF, rhoERF, &mesh.normals(i), 
                rhoFlux, rhoUFlux, rhoEFlux);
            this->operate->div(&rhoFlux, drho, i, neighbour);
            this->operate->div(rhoUFlux, drhoU, i, neighbour);
            this->operate->div(&rhoEFlux, drhoE, i, neighbour);
        }
    };
    faceFluxUpdate(0, mesh.nInternalFaces, true);
    //cout << "c++: equation 4" << endl;
    // characteristic boundary
    for (auto& patch: mesh.boundary) {
        auto& patchInfo = patch.second;
        integer startFace, nFaces;
        tie(startFace, nFaces) = mesh.boundaryFaces.at(patch.first);
        integer cellStartFace = mesh.nInternalCells + startFace - mesh.nInternalFaces;
        if (patchInfo.at("type") == "cyclic") {
            faceFluxUpdate(startFace, startFace + nFaces, false);
        } else {
            for (integer i = 0; i < nFaces; i++) {
                integer index = startFace + i;
                integer c = cellStartFace + i;
                scalar rhoFlux;
                scalar rhoUFlux[3];
                scalar rhoEFlux;
                this->getFlux(&U(c), T(c), p(c), &mesh.normals(index), rhoFlux, rhoUFlux, rhoEFlux);
                this->operate->div(&rhoFlux, drho, index, false);
                this->operate->div(rhoUFlux, drhoU, index, false);
                this->operate->div(&rhoEFlux, drhoE, index, false);
            }
        }
    }
    faceFluxUpdate(mesh.nLocalFaces, mesh.nFaces, false);
    //cout << "c++: equation 5" << endl;
}

void RCF::boundary(const Boundary& boundary, arr& phi) {
    const Mesh& mesh = *this->mesh;
    //MPI_Barrier(MPI_COMM_WORLD);

    arr phiBuf(mesh.nCells-mesh.nLocalCells, phi.shape[1], phi.shape[2]);
    AMPI_Request* req;
    integer reqIndex = 0;
    if (mesh.nRemotePatches > 0) {
        req = new AMPI_Request[2*mesh.nRemotePatches];
    }

    for (auto& patch: boundary) {
        string patchType = patch.second.at("type");
        string patchID = patch.first;
        const map<string, string>& patchInfo = mesh.boundary.at(patchID);

        integer startFace, nFaces;
        tie(startFace, nFaces) = mesh.boundaryFaces.at(patch.first);
        integer cellStartFace = mesh.nInternalCells + startFace - mesh.nInternalFaces;

        if (patchType == "cyclic") {
            string neighbourPatchID = patchInfo.at("neighbourPatch");
            integer neighbourStartFace = std::get<0>(mesh.boundaryFaces.at(neighbourPatchID));
            for (integer i = 0; i < nFaces; i++) {
                integer p = mesh.owner(neighbourStartFace + i);
                integer c = cellStartFace + i;
                for (integer j = 0; j < phi.shape[1]; j++) {
                    for (integer k = 0; k < phi.shape[2]; k++) {
                        phi(c, j, k) = phi(p, j, k);
                    }
                }
            }
        } else if (patchType == "zeroGradient" || patchType == "empty" || patchType == "inletOutlet") {
            for (integer i = 0; i < nFaces; i++) {
                integer p = mesh.owner(startFace + i);
                integer c = cellStartFace + i;
                for (integer j = 0; j < phi.shape[1]; j++) {
                    for (integer k = 0; k < phi.shape[2]; k++) {
                        phi(c, j, k) = phi(p, j, k);
                    }
                }
            }
        } else if (patchType == "symmetryPlane" || patchType == "slip") {
            if ((phi.shape[1] == 3) && (phi.shape[2] == 1)) {
                for (integer i = 0; i < nFaces; i++) {
                    integer f = startFace + i;
                    integer c = cellStartFace + i;
                    integer p = mesh.owner(f);
                    scalar phin = 0.;
                    for (integer j = 0; j < 3; j++) {
                        phin += mesh.normals(f, j)*phi(p, j);
                    }
                    for (integer j = 0; j < 3; j++) {
                        phi(c, j) = phi(p, j) - mesh.normals(f, j)*phin;
                    }
                }
            } else {
                for (integer i = 0; i < nFaces; i++) {
                    integer p = mesh.owner(startFace + i);
                    integer c = cellStartFace + i;
                    for (integer j = 0; j < phi.shape[1]; j++) {
                        for (integer k = 0; k < phi.shape[2]; k++) {
                            phi(c, j, k) = phi(p, j, k);
                        }
                    }
                }
            }
        } else if (patchType == "fixedValue") {
            // fix this
            // more boundary conditions
            if (phi.shape[1] == 3) {
                for (integer i = 0; i < nFaces; i++) {
                    phi(cellStartFace + i, 0) = 3.;
                    phi(cellStartFace + i, 1) = 0.;
                    phi(cellStartFace + i, 2) = 0.;
                } 
            } else {
                for (integer i = 0; i < nFaces; i++) {
                    phi(cellStartFace + i) = 1.;
                }
            }
        } else if (patchType == "processor" || patchType == "processorCyclic") {
            //cout << "hello " << patchID << endl;
            integer bufStartFace = cellStartFace - mesh.nLocalCells;
            integer size = nFaces*phi.shape[1]*phi.shape[2];
            integer dest = stoi(patchInfo.at("neighbProcNo"));
            integer tag = 0;
            for (integer i = 0; i < nFaces; i++) {
                integer p = mesh.owner(startFace + i);
                integer b = bufStartFace + i;
                for (integer j = 0; j < phi.shape[1]; j++) {
                    for (integer k = 0; k < phi.shape[2]; k++) {
                        phiBuf(b, j, k) = phi(p, j, k);
                    }
                }
            }
            AMPI_Isend(&phiBuf(bufStartFace), size, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD, &req[reqIndex]);
            AMPI_Irecv(&phi(cellStartFace), size, MPI_DOUBLE, dest, tag, MPI_COMM_WORLD, &req[reqIndex+1]);
            reqIndex += 2;
        }
        else {
            cout << "patch not found " << patchType << " for " << patchID << endl;
        }
    }
    if (mesh.nRemotePatches > 0) {
        AMPI_Waitall(2*mesh.nRemotePatches, req, MPI_STATUSES_IGNORE);
        delete[] req;
    }
}

